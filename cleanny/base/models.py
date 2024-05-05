from django.db import models
# Create your models here.


class Client(models.Model):
    tg_nickname = models.CharField(max_length=128, blank=True, null=True)
    tel = models.IntegerField()
    adress = models.CharField(max_length=256)
    chat_id = models.IntegerField()

    def __str__(self):
        return str(self.chat_id)


class Order(models.Model):
    client_id = models.ForeignKey(Client, on_delete=models.CASCADE)
    time_placed = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField()
    is_aborted = models.BooleanField()
    total_price = models.FloatField()
    datetime_start = models.DateTimeField()
    datetime_end = models.DateTimeField()

    def __str__(self):
        return str(self.client_id) + ' / ' + str(self.datetime_start)[:19] + ' / ' + self.client_id.adress

class Equip(models.Model):
    name = models.CharField(max_length=256)
    is_consumable = models.BooleanField()
    is_expire = models.BooleanField()
    units = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Storage_full(models.Model):
    equip_id = models.ForeignKey(Equip, on_delete=models.PROTECT)
    amount = models.IntegerField()
    expire_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.equip_id) + " / " + str(self.amount) + " / " + 'expires:' + str(self.expire_date)

    class Meta:
        verbose_name_plural = "Storage_full"


class Storage_active(models.Model):
    equip_id = models.ForeignKey(Equip, on_delete=models.PROTECT)
    amount = models.IntegerField()
    expire_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.equip_id) + " / " + str(self.amount) + " / " + 'expires:' + str(self.expire_date)

    class Meta:
        verbose_name_plural = "Storage_active"




class Employee(models.Model):
    name = models.CharField(max_length=256)
    tg_id = models.IntegerField()
    google_account = models.CharField(max_length=256)
    dob = models.DateField()

    def __str__(self):
        return str(self.name) + ' ' + str(self.dob)


class Employees_list(models.Model):
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    employee_id = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.order_id) + " / " + self.employee_id.name


class Review(models.Model):
    employee_id = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)
    client_id = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True)
    message = models.TextField()

    def __str__(self):
        return str(self.client_id) + " / " + str(self.employee_id)

class Equip_list(models.Model):
    equip_id = models.ForeignKey(Equip, on_delete=models.PROTECT)
    amount = models.IntegerField()
    employee_id = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.equip_id) + " / " + self.employee_id.name


class Service(models.Model):
    name = models.CharField(max_length=256)
    price = models.FloatField()
    time = models.TimeField()
    min_number = models.IntegerField()
    max_number = models.IntegerField()

    def __str__(self):
        return self.name


class Service_req(models.Model):
    equip_id = models.ForeignKey(Equip, on_delete=models.PROTECT)
    amount = models.IntegerField()
    service_id = models.ForeignKey(Service, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.service_id) + " / " + self.equip_id.name + ' X ' + str(self.amount)


class Services_list(models.Model):
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    service_id = models.ForeignKey(Service, on_delete=models.PROTECT)
    amount = models.IntegerField()

    def __str__(self):
        return str(self.order_id) + " / " + self.service_id.name



from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


# @receiver(post_save, sender=Client)
# def umnaya_funktsiya(**kwargs):
#     pass
