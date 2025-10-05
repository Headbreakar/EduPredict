from django.db import models

# Create your models here.
class Signup(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    usertype = models.CharField(max_length=20, choices=[("admin","Admin"),("teacher","Teacher"),("student","Student")])
    
    # Student-specific
    class_name = models.CharField(max_length=50, null=True, blank=True)
    roll_no = models.CharField(max_length=50, null=True, blank=True)

    # Teacher-specific
    subject = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class Feedback(models.Model) : 
    name = models.CharField(max_length=100) 
    email = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.CharField(max_length=100)
    fkuser = models.ForeignKey(Signup,on_delete=models.CASCADE)
