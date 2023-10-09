from django.db import models

class CompressedImage(models.Model):
    image = models.ImageField(upload_to='images/')
