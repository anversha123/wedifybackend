from django.db import models

class Planner(models.Model):
    name = models.CharField(max_length=255)
    contact = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    basePrice = models.IntegerField()
    description = models.TextField()
    image = models.URLField(max_length=500, blank=True, null=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True) # Storing plain for now as per legacy localstorage, but ideally hash.

    def __str__(self):
        return self.name

class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    planner = models.ForeignKey(Planner, on_delete=models.CASCADE, null=True, blank=True)
    plannerName = models.CharField(max_length=255, null=True, blank=True) # Redundant but helps if FK is missing or for quick display
    venueId = models.IntegerField(null=True, blank=True) # Legacy field
    userEmail = models.EmailField()
    date = models.CharField(max_length=50)
    guestCount = models.IntegerField()
    requirements = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    totalPrice = models.IntegerField(null=True, blank=True)
    paymentStatus = models.CharField(max_length=20, default='unpaid', null=True, blank=True)
    paymentMethod = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Booking {self.id} - {self.userEmail}"
