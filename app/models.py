import os

from werkzeug.security import generate_password_hash, check_password_hash
from app import db, app
import json


class New(db.Model):
    __tablename__ = "news"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    publication_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.String(1000), nullable=False)


class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(50), nullable=False)
    street_ru = db.Column(db.String(150), nullable=False)
    home = db.Column(db.String(15), nullable=False)
    bulk = db.Column(db.String(10), nullable=False)


class PayPeriod(db.Model):
    __tablename__ = "pay_period"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    year = db.Column(db.String(4), nullable=False)
    month_number = db.Column(db.String(2), nullable=False)
    month_name_ru = db.Column(db.String(10), nullable=False)


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(50), nullable=False)
    name_ru = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    deleted = db.Column(db.Boolean, nullable=False, default=False)


# Квитанция на оплату
class Stub(db.Model):
    __tablename__ = "stubs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sum = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.String(50), nullable=False)
    debt = db.Column(db.String(50), nullable=False)

    id_service = db.Column(db.Integer, db.ForeignKey("services.id"))
    id_period = db.Column(db.Integer, db.ForeignKey("pay_period.id"))
    id_renter = db.Column(db.Integer, db.ForeignKey("renters.id"))


# Тарифы
class Rate(db.Model):
    __tablename__ = "rates"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sum = db.Column(db.String(10), nullable=False)

    id_service = db.Column(db.Integer, db.ForeignKey("services.id"))
    id_address = db.Column(db.Integer, db.ForeignKey("addresses.id"))
    id_period = db.Column(db.Integer, db.ForeignKey("pay_period.id"))


class Role(db.Model):
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(10), nullable=False)
    admin = db.Column(db.Boolean, nullable=False)


# Жилец
# account - номер лицевого счета
# float - квартира
# floorspace - жилая площадь
# floorarea - общая площадь
class Renter(db.Model):
    __tablename__ = "renters"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    account = db.Column(db.String(50), nullable=False)
    float = db.Column(db.String(50), nullable=False)
    floor_space = db.Column(db.String(10), nullable=False)
    floor_area = db.Column(db.String(10), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    id_address = db.Column(db.Integer, db.ForeignKey("addresses.id"))
    id_role = db.Column(db.Integer, db.ForeignKey("role.id"))

    @property
    def password(self):
        # Запретим прямое обращение к паролю
        raise AttributeError("Вам не нужно знать пароль!")

    @password.setter
    def password(self, password):
        # Устанавливаем пароль через этот метод
        self.password_hash = generate_password_hash(password)

    def password_valid(self, password):
        # Проверяем пароль через этот метод
        # Функция check_password_hash превращает password в хеш и сравнивает с хранимым
        return check_password_hash(self.password_hash, password)


def upload_data_from_db():
    with open(
            os.path.join(app.config["UPLOAD_FOLDER"], app.config["FILENAME_IMPORT"]),
            "r",
            encoding="utf-8",
            ) as f:
        contents = f.read()

    my_list = json.loads(contents)

    # Pay period
    year_pay = ["2019", "2020"]
    for y in year_pay:
        year = PayPeriod.query.filter_by(year=y).first()
        if year is None:
            for m in my_list["month_name"]:
                period = PayPeriod()
                period.month_number = str(m["month_number"])
                period.month_name_ru = m["month_name_ru"]
                period.year = y
                db.session.add(period)

    # Address
    for building in my_list["building"]:
        uid = building["uid"]
        if Address.query.filter_by(uid=uid).first() is None:
            address = Address()
            address.uid = uid
            address.street_ru = building["street"]
            address.home = building["home"]
            address.bulk = building["bulk"]

            db.session.add(address)

    # Service
    for s in my_list["service"]:
        uid = s["uid"]

        if (
                Service.query.filter_by(uid=uid).first() is None
                and Service.query.filter_by(name_ru=s["name"]).first() is None
        ):
            service = Service()
            service.uid = s["uid"]
            service.name_ru = s["name"]
            service.unit = s["unit"]

            db.session.add(service)

    db.session.commit()

    # Rate
    for r in my_list["rate"]:
        address = Address.query.filter_by(uid=r["uid_address"]).first()
        service = Service.query.filter_by(uid=r["uid_service"]).first()

        if address is None or service is None:
            continue

        for r_p in r["rate_period"]:
            id_period = PayPeriod.query.filter_by(
                    month_number=str(r_p["month"]),
                    year=r_p["year"]
                    ).first()

            rate_in_db = Rate.query.filter_by(
                    id_address=address.id,
                    id_service=service.id,
                    id_period=id_period.id
                    ).first()

            if rate_in_db is None:
                rate = Rate()
                rate.id_address = address.id
                rate.id_service = service.id
                rate.id_period = id_period.id
                rate.sum = r_p["sum"]
                db.session.add(rate)
            else:
                rate_in_db.sum = r_p["sum"]

    # Renter
    for r in my_list["renters"]:
        uid = r["uid"]

        if Renter.query.filter_by(uid=uid).first() is not None:
            renter = Renter.query.filter_by(uid=uid).first()
        else:
            renter = Renter()

        address = Address.query.filter_by(uid=r["building"]).first()
        if address is None:
            continue

        renter.id_address = address.id
        renter.uid = uid
        renter.name = r["name"]
        renter.account = r["account"]
        renter.float = r["float"]
        renter.floor_area = r["floorarea"]
        try:
            renter.floor_space = r["floorspace"]
        except KeyError:
            renter.floor_space = 0

        renter.password_hash = " "

        db.session.add(renter)

    db.session.commit()

    # Stubs
    for s in my_list["stubs"]:
        renter = Renter.query.filter_by(uid=s["account"]).first()

        if renter is None:
            continue

        period = PayPeriod.query.filter_by(
                month_number=my_list["period"][0]["month"],
                year=my_list["period"][0]["year"],
                ).first()

        if period is None:
            continue

        for stb in s["stubs"]:
            service = Service.query.filter_by(uid=stb["service"]).first()
            if service is None:
                continue

            find_stub = Stub.query.filter_by(
                    id_renter=renter.id,
                    id_period=period.id,
                    id_service=service.id
                    ).first()
            if find_stub is None:
                stub = Stub()
            else:
                stub = find_stub

            stub.id_period = period.id
            stub.id_service = service.id
            stub.id_renter = renter.id

            stub.sum = stb["sum"]
            stub.debt = stb["debt"]
            stub.amount = stb["amount"]

            db.session.add(stub)

    db.session.commit()
    f.close()
