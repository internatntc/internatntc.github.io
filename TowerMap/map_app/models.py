from django.db import models


class Tower(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name


class UserCell(models.Model):
    tower = models.ForeignKey(Tower, on_delete=models.CASCADE)
    cell_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return f"{self.cell_number} (Tower: {self.tower.name})"
