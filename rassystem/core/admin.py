from django.contrib import admin

# Register your models here.
from core.models import Company, Call, Service, Location, Vehicle


class CompanyAdmin(admin.ModelAdmin):
    pass


class CallAdmin(admin.ModelAdmin):
    pass


class ServiceAdmin(admin.ModelAdmin):
    pass


class LocationAdmin(admin.ModelAdmin):
    pass


class VehicleAdmin(admin.ModelAdmin):
    pass


admin.site.register(Company, CompanyAdmin)
admin.site.register(Call, CallAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Vehicle, VehicleAdmin)
