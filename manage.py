from sqlalchemy.orm import make_transient
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import random
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:KappaPride@localhost/car_database'
db = SQLAlchemy(app)

class CarModelEnum(Enum):
    MODEL_A = "Модель A"
    MODEL_B = "Модель B"
    MODEL_C = "Модель C"

class CarConfiguration(Enum):
    BASE = "Базовая"
    COMFORT = "Комфорт"
    MAXIMUM = "Максимальная"

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.Enum(CarModelEnum), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), nullable=False)
    engine_power = db.Column(db.Integer, nullable=False)
    vin = db.Column(db.String(17), unique=True, nullable=False)
    configuration = db.Column(db.Enum(CarConfiguration), nullable=False)
    description = db.Column(db.Text)

@app.route('/cars', methods=['GET'])
def get_cars():
    try:
        cars = Car.query.all()
        car_list = []
        for car in cars:
            car_data = {
                'id': car.id,
                'brand': car.brand,
                'model': car.model.value,
                'year': car.year,
                'color': car.color,
                'engine_power': car.engine_power,
                'vin': car.vin,
                'configuration': car.configuration.value,
                'description': car.description
            }
            car_list.append(car_data)
        return jsonify({'cars': car_list})
    except Exception as e:
        return jsonify({'error_message': str(e)}), 500

@app.route('/cars', methods=['POST'])
def add_car():
    try:
        data = request.get_json()

        model_value = data['model']
        configuration_value = data['configuration']

        try:
            model_enum = CarModelEnum(model_value)
        except ValueError:
            return jsonify({'message': 'Invalid model value'}), 400

        try:
            configuration_enum = CarConfiguration(configuration_value)
        except ValueError:
            return jsonify({'message': 'Invalid configuration value'}), 400
        
        vin_pattern = "WDDUJ76X09A000000"
        vin_number = re.sub(r'[A-Z]', lambda x: random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), vin_pattern)
        vin_number = re.sub(r'[0-9]', lambda x: str(random.randint(0, 9)), vin_number)

        new_car = Car(
            brand=data['brand'],
            model=model_enum,
            year=data['year'],
            color=data['color'],
            engine_power=data['engine_power'],
            vin=vin_number,
            configuration=configuration_enum,
            description=data.get('description')
        )
        
        with app.app_context():
            db.session.add(new_car)
            db.session.commit()
        
        return jsonify({'message': 'Car added successfully'}), 201
    except Exception as e:
        return jsonify({'error_message': str(e)}), 500

@app.route('/cars/<int:car_id>', methods=['PUT'])
def edit_car(car_id):
    try:
        car = Car.query.get(car_id)

        if car is None:
            return jsonify({'message': 'Car not found'}), 404

        data = request.get_json()
        model_value = data.get('model')
        configuration_value = data.get('configuration')

        try:
            if model_value:
                model_enum = CarModelEnum(model_value)
            else:
                model_enum = car.model

            if configuration_value:
                configuration_enum = CarConfiguration(configuration_value)
            else:
                configuration_enum = car.configuration
        except ValueError:
            return jsonify({'message': 'Invalid model or configuration value'}), 400

        with app.app_context():
            make_transient(car)
            updated_car = Car(
                id=car.id,
                brand=data.get('brand', car.brand),
                model=model_enum,
                year=data.get('year', car.year),
                color=data.get('color', car.color),
                engine_power=data.get('engine_power', car.engine_power),
                vin=data.get('vin', car.vin),
                configuration=configuration_enum,
                description=data.get('description', car.description)
            )

            db.session.merge(updated_car)
            db.session.commit()

        return jsonify({'message': 'Car updated successfully'})
    except Exception as e:
        return jsonify({'error_message': str(e)}), 500

@app.route('/cars/<int:car_id>', methods=['DELETE'])
def delete_car(car_id):
    try:
        car = Car.query.get(car_id)
        if car is None:
            return jsonify({'message': 'Car not found'}), 404

        with app.app_context():
            existing_car = db.session.query(Car).filter_by(id=car_id).first()
            if existing_car:
                db.session.delete(existing_car)
                db.session.commit()
                return jsonify({'message': 'Car deleted successfully'})
            else:
                return jsonify({'message': 'Car not found'}), 404
    except Exception as e:
        return jsonify({'error_message': str(e)}), 500

@app.route('/cars/delete-all', methods=['DELETE'])
def delete_all_cars():
    try:
        with app.app_context():
            db.session.query(Car).delete()
            db.session.commit()
        return jsonify({'message': 'All cars deleted successfully'})
    except Exception as e:
        return jsonify({'error_message': str(e)}), 500

if __name__ == '__main__':
    app.config['SQLALCHEMY_ECHO'] = True
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)