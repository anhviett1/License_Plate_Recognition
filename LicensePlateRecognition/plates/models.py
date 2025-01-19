from django.db import models

class LicensePlate(models.Model):
    plate_number = models.CharField(max_length=15, unique=True)
    detected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.plate_number



