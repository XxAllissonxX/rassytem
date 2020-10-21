from django.db import models


class Company(models.Model):
    name = models.CharField(verbose_name='Nome', max_length=100)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    licence_plate = models.CharField(verbose_name='Placa', max_length=8)
    company = models.ForeignKey('Company', on_delete=models.CASCADE)

    def __str__(self):
        return self.licence_plate


class Location(models.Model):
    vehicle = models.OneToOneField('Vehicle', on_delete=models.CASCADE)
    latitude = models.CharField(verbose_name='Latitude', max_length=20)
    longitude = models.CharField(verbose_name='Longitude', max_length=20)

    def __str__(self):
        return '{} - {}, {}'.format(self.vehicle.licence_plate,
                                    self.latitude, self.longitude)


class Service(models.Model):
    name = models.CharField(verbose_name='Nome do serviço', max_length=50)
    location = models.ForeignKey('Location', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Call(models.Model):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    kind = models.CharField(verbose_name='Tipo', max_length=50)
    call_date = models.DateTimeField(verbose_name='Data da Chamada')

    def __str__(self):
        return '{} - {} - {}'.format(self.call_date,
                                     self.kind, self.company.name)
