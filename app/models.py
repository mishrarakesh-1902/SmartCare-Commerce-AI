from django.db import models

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
import datetime




# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name
 
class Sub_category(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category , on_delete=models.CASCADE )


    def __str__(self):
        return self.name

#brand models to fetch database 
 
class Brand(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    
class Product(models.Model):
    Availability = (('In Stock' , 'In Stock') , ('Out of Stock' , 'Out of Stock'))

    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False, default='')
    sub_category= models.ForeignKey(Sub_category, on_delete=models.CASCADE , null=False, default='')
    brand = models.ForeignKey(Brand , on_delete=models.CASCADE ,null=True)
    image = models.ImageField(upload_to='ecommerce/pimg')
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    Availability = models.CharField(choices=Availability, null=True , max_length=1000)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_gallery_images(self):
        """
        Returns an ordered list of image dicts:
        [{'url': '/ecommerce/pimg/...', 'alt': 'Front Angle', 'label': 'Front', 'angle': 'Front View'}]
        Combines the primary image with any additional uploaded angle images.
        """
        gallery = []
        if self.image:
            gallery.append({
                'url': f"/{self.image}",
                'alt': f"{self.name} - Front View",
                'label': 'Front',
                'angle': 'Primary / Front View'
            })
        for idx, item in enumerate(self.additional_images.all(), start=1):
            if item.image:
                label = item.alt_text or f"Angle {idx + 1}"
                gallery.append({
                    'url': f"/{item.image}",
                    'alt': f"{self.name} - {label}",
                    'label': label,
                    'angle': item.alt_text or f"Perspective {idx + 1}"
                })
        
        # Smart fallback: if only 1 image exists, pull complementary angle perspectives
        if len(gallery) < 2 and (self.sub_category_id or self.category_id):
            perspective_names = ["Side Profile Angle", "Back Angle", "Texture & Detail", "Perspective View"]
            qs = Product.objects.exclude(id=self.id)
            if self.sub_category_id:
                related_imgs = list(qs.filter(sub_category_id=self.sub_category_id).values_list('image', flat=True)[:3])
            else:
                related_imgs = list(qs.filter(category_id=self.category_id).values_list('image', flat=True)[:3])
            
            for i, r_img in enumerate(related_imgs):
                if r_img:
                    lbl = perspective_names[i % len(perspective_names)]
                    gallery.append({
                        'url': f"/{r_img}",
                        'alt': f"{self.name} - {lbl}",
                        'label': lbl,
                        'angle': lbl
                    })
        return gallery


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='additional_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='ecommerce/pimg')
    alt_text = models.CharField(max_length=150, blank=True, null=True, help_text="e.g. Back View, Side Profile, Detail Close-up")
    order = models.PositiveIntegerField(default=0, help_text="Order in gallery")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Product Image"
        verbose_name_plural = "Product Additional Images"

    def __str__(self):
        return f"{self.product.name} - {self.alt_text or 'Image Angle'}"


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required = True , label='Email' , error_messages={'exists': 'This Already Exists'})

    class Meta:
        model = User
        fields = ('username' , 'email', 'password1','password2')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adding placeholders and CSS classes to each field
        self.fields['username'].widget.attrs.update({'placeholder': 'User Name', 'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Email Address', 'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password', 'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password', 'class': 'form-control'})    


        def save(self, commit=True):
            user = super(UserCreateForm,self).save(commit=False)
            user.email= self.cleaned_data['email']
            if commit:
                user.save()
            return user
        
        def clean_email(self):
            if User.objects.filter(email=self.cleaned_data['email']).exists():
                raise forms.ValidationError(self.fields['email'].error_message['exists'])
            return self.cleaned_data['email']
        


class Contact_us(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.TextField()


    def __str__(self):
        return self.email
    


class Order(models.Model):
    image = models.ImageField(upload_to='ecommerce/order/image')
    product = models.CharField(max_length=1000 , default='')
    user = models.ForeignKey(User , on_delete=models.CASCADE)
    price = models.IntegerField()
    quantity = models.CharField(max_length=5)
    total = models.CharField(max_length=10000000 , default='')
    address = models.TextField()
    phone = models.CharField(max_length=10)
    pincode = models.CharField(max_length=10)
    
    date = models.DateField(default=datetime.datetime.today)
    

    def __str__(self):
        return self.product
    




class Feedback(models.Model):
    brand_name = models.CharField(max_length=100)
    product_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.IntegerField(choices=[(1, '⭐'), (2, '⭐⭐'), (3, '⭐⭐⭐'), (4, '⭐⭐⭐⭐'), (5, '⭐⭐⭐⭐⭐')])
    comments = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.brand_name} - {self.rating} Stars"


class SupportTicket(models.Model):
    ticket_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    urgency = models.CharField(max_length=50, blank=True, null=True)
    sentiment = models.CharField(max_length=50, blank=True, null=True)
    action = models.CharField(max_length=100, blank=True, null=True)
    ai_response = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='resolved')
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.ticket_id} - {self.subject} ({self.status})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    avatar = models.ImageField(upload_to='ecommerce/profile_pics/', blank=True, null=True)
    bio = models.CharField(max_length=255, blank=True, null=True, default="Valued Shopper")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def full_name(self):
        name = f"{self.user.first_name} {self.user.last_name}".strip()
        return name if name else self.user.username

    @property
    def initials(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        elif self.user.first_name:
            return self.user.first_name[:2].upper()
        return self.user.username[:2].upper()


def get_or_create_user_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    if created or not profile.address:
        last_order = Order.objects.filter(user=user).order_by('-id').first()
        if last_order:
            changed = False
            if not profile.phone and last_order.phone:
                profile.phone = last_order.phone
                changed = True
            if not profile.address and last_order.address:
                profile.address = last_order.address
                changed = True
            if not profile.pincode and last_order.pincode:
                profile.pincode = last_order.pincode
                changed = True
            if changed:
                profile.save()
    return profile
