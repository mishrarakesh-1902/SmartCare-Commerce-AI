"""
URL configuration for E_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from .import views





#yaha v naya code  h 

from .views import feedback_view, feedback_success


#naya code h
# from django.urls import path
# from .views import checkout, paytm_response
from django.urls import path
from .views import initiate_paytm_payment, paytm_response


urlpatterns = [
    path('admin/', admin.site.urls),
    path('master/' , views.Master , name='master'),
    path('' , views.Index,name='index'),
   
    path('signup' , views.signup , name='signup'),
    path('accounts/', include('django.contrib.auth.urls')), 
   
     
     #addtocart function setting

    path('cart/add/<int:id>/', views.cart_add, name='cart_add'),
    path('cart/item_clear/<int:id>/', views.item_clear, name='item_clear'),
    path('cart/item_increment/<int:id>/',
         views.item_increment, name='item_increment'),
    path('cart/item_decrement/<int:id>/',
         views.item_decrement, name='item_decrement'),
    path('cart/cart_clear/', views.cart_clear, name='cart_clear'),
    path('cart/cart-detail/',views.cart_detail,name='cart_detail'),
    
#contact page url setting
    path('contact_us/' , views.Contact_Page, name="contact_page"),

    #cheakout page url setting
    path('cheakout/' , views.CheakOut , name="cheakout"),

    #order page
    path('order/' , views.Your_Order , name="order"),

    #product page url setting
    path('product/' , views.Product_page , name="product"),

    #pruduct_details url setup
    path('product/<str:id>', views.Product_Detail, name="product_detail"),
    path('product/<str:id>/', views.Product_Detail),
    path('<int:id>', views.Product_Detail, name="product_detail_direct"),
    path('<int:id>/', views.Product_Detail),

    #peivacy
    path('privecy/' , views.Privecy , name="privecy"),

    #search page url setup
    path('search/' , views.Search , name="search"),


    # naya code h 
    # path("checkout/", checkout, name="checkout"),
    # path("paytm-response/", paytm_response, name="paytm_response"),
    path("initiate-payment/", initiate_paytm_payment, name="initiate_paytm_payment"),
    path("paytm-response/", paytm_response, name="paytm_response"),
   

    path('feedback/', feedback_view, name='feedback'),
    path('feedback-success/', feedback_success, name='feedback_success'),   

    # Autonomous AI Customer Support Helpdesk
    path('ai-support/', views.ai_support_view, name='ai_support'),
    path('ai-support/ticket/<str:ticket_id>/', views.ticket_detail_view, name='ticket_detail'),

    # Customer Account Profile
    path('profile/', views.profile_view, name='user_profile'),



] + static(settings.MEDIA_URL , document_root = settings.MEDIA_ROOT)

















