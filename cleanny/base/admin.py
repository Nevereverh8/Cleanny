from django.contrib import admin
from .models import *
# Register your models here.



admin.site.register(Storage_active)
admin.site.register(Employee)
admin.site.register(Equip)
admin.site.register(Order)
admin.site.register(Service)
admin.site.register(Services_list)
admin.site.register(Service_req)
admin.site.register(Employees_list)
admin.site.register(Review)
admin.site.register(Equip_list)
admin.site.register(Storage_full)


class ClientAdmin(admin.ModelAdmin):
    fields = ["tg_nickname", 'tel', 'adress', 'chat_id']
    list_display = ["tg_nickname", 'tel', 'adress', 'chat_id']
    list_filter = ['tg_nickname']
    readonly_fields = ['chat_id']
    list_editable = ['tel']
    # tg_nickname = models.CharField(max_length=128)
    # tel = models.IntegerField()
    # adress = models.CharField(max_length=256)
    # chat_id = models.IntegerField()



admin.site.register(Client, ClientAdmin)
