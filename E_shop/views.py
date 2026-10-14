from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from app.models import Category, Product, Sub_category, Contact_us, Order, Brand, SupportTicket
from django.contrib.auth import authenticate, login
from app.models import UserCreateForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from cart.cart import Cart

from app.forms import FeedbackForm

import json
import requests

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paytmchecksum import generateSignature, verifySignature


def Master(request):
    return render(request, 'master.html')

def Index(request):
    category = Category.objects.prefetch_related('sub_category_set').all()
    brand = Brand.objects.all()
    
    brandID = request.GET.get('brand')
    categoryID = request.GET.get('category')
    subCategoryID = request.GET.get('sub_category')

    products = Product.objects.all().select_related('category', 'sub_category', 'brand').order_by('-id')

    active_category = None
    active_sub_category = None
    active_brand = None

    if subCategoryID:
        products = products.filter(sub_category_id=subCategoryID)
        active_sub_category = Sub_category.objects.filter(id=subCategoryID).first()
        if active_sub_category:
            active_category = active_sub_category.category
    elif categoryID:
        products = products.filter(category_id=categoryID)
        active_category = Category.objects.filter(id=categoryID).first()

    if brandID:
        products = products.filter(brand_id=brandID)
        active_brand = Brand.objects.filter(id=brandID).first()

    # Pre-filtered products for the curated trending section on homepage
    trending_tshirts = Product.objects.filter(sub_category__name__iexact='T-shirt').order_by('-id')[:4]
    if not trending_tshirts.exists():
        trending_tshirts = Product.objects.filter(name__icontains='T-shirt')[:4]
    trending_women = Product.objects.filter(category__name__icontains='women').order_by('-id')[:4]
    trending_tech = Product.objects.filter(category__name__icontains='mobile').order_by('-id')[:4]
    trending_home = Product.objects.filter(category__name__icontains='home').order_by('-id')[:4]

    context = {
        'category': category,
        'product': products,
        'brand': brand,
        'active_category': active_category,
        'active_sub_category': active_sub_category,
        'active_brand': active_brand,
        'trending_tshirts': trending_tshirts,
        'trending_women': trending_women,
        'trending_tech': trending_tech,
        'trending_home': trending_home,
    }
    return render(request, 'index.html', context)
def signup(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user = authenticate(
                username = form.cleaned_data['username'],
                password = form.cleaned_data['password1'],
            )
            
            login(request , new_user)
            return redirect('index')
        
    else:
        form = UserCreateForm()

    context = {
        'form' : form,
    }    

    return render(request, 'registration/signup.html',context)



@login_required(login_url='/accounts/login/')
def cart_add(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)

    # If AJAX request, return JSON so page doesn't even reload
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        cart_count = len(request.session.get('cart', {}))
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart!',
            'cart_count': cart_count,
            'product_name': product.name,
            'product_price': product.price,
        })

    # Keep customer on the exact same page they clicked from
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect("product")


@login_required(login_url='/accounts/login/')
def item_clear(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.remove(product)
    return redirect("cart_detail")


@login_required(login_url='/accounts/login/')
def item_increment(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.add(product=product)
    return redirect("cart_detail")


@login_required(login_url='/accounts/login/')
def item_decrement(request, id):
    cart = Cart(request)
    product = Product.objects.get(id=id)
    cart.decrement(product=product)
    return redirect("cart_detail")


@login_required(login_url='/accounts/login/')
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return redirect("cart_detail")

@login_required(login_url='/accounts/login/')
def cart_detail(request):
    return render(request, 'cart/cart_detail.html')

def Contact_Page(request):
    if request.method == "POST":
        contact = Contact_us(
            name = request.POST.get('name'),
            email = request.POST.get('email'),
            subject = request.POST.get('subject'),
            message = request.POST.get('message'),
        )
        contact.save()
    return render(request,'contact.html')

@login_required(login_url='/accounts/login/')
def CheakOut(request):
    if request.method == "POST":
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        pincode = request.POST.get('pincode')
        cart = request.session.get('cart', {})
        user = request.user

        for i in cart:
            try:
                a = int(cart[i]['price'])
                b = int(cart[i]['quantity'])
                total = a * b
                order = Order(
                    user = user,
                    product = cart[i]['name'],
                    price = cart[i]['price'],
                    quantity = cart[i]['quantity'],
                    image = cart[i]['image'],
                    address = address,
                    phone = phone,
                    pincode = pincode,
                    total = str(total),
                )
                order.save()
            except Exception as e:
                print("Error creating order:", e)

        request.session['cart'] = {}    
        return redirect("order")

    return HttpResponse("Your order has been placed")


@login_required(login_url='/accounts/login/')
def Your_Order(request):
    user = request.user
    order = Order.objects.filter(user = user).order_by('-id')
    context = {
        'order' : order,
    }
    return render(request , 'order.html' , context)

def Product_page(request):
    category = Category.objects.prefetch_related('sub_category_set').all()
    brand = Brand.objects.all()
    brandID = request.GET.get('brand')
    categoryID = request.GET.get('category')
    subCategoryID = request.GET.get('sub_category')

    products = Product.objects.all().select_related('category', 'sub_category', 'brand').order_by('-id')

    active_category = None
    active_sub_category = None
    active_brand = None

    if subCategoryID:
        products = products.filter(sub_category_id=subCategoryID)
        active_sub_category = Sub_category.objects.filter(id=subCategoryID).first()
        if active_sub_category:
            active_category = active_sub_category.category
    elif categoryID:
        products = products.filter(category_id=categoryID)
        active_category = Category.objects.filter(id=categoryID).first()

    if brandID:
        products = products.filter(brand_id=brandID)
        active_brand = Brand.objects.filter(id=brandID).first()

    context = {
        'category': category,
        'brand': brand,
        'product': products,
        'active_category': active_category,
        'active_sub_category': active_sub_category,
        'active_brand': active_brand,
    }
    return render(request, 'product.html', context)


def Product_Detail(request , id):
    product = Product.objects.filter(id = id).first()
    category = Category.objects.all()
    brand = Brand.objects.all()
    related_products = []
    if product:
        if product.category:
            related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
        if not related_products:
            related_products = Product.objects.exclude(id=product.id)[:4]
    
    context = {
        'product': product,
        'category': category,
        'brand': brand,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)

def Search(request):
    category = Category.objects.all()
    brand = Brand.objects.all()
    query = request.GET.get('query')
    if query:
        product = Product.objects.filter(name__icontains = query)
    else:
        product = Product.objects.none()

    context = {
        'category': category,
        'brand': brand,
        "product": product,
    }

    return render(request, 'search.html' , context) 

def Privecy(request):


    context ={
        
    }
    return render(request, 'privecy.html',context)



def initiate_paytm_payment(request):
    if request.method == "POST":
        amount = request.session.get("cart_total_amount", 0)  # Fetch total amount from session
        order_id = str(request.user.id) + "ORD" + str(request.session.session_key)

        # Paytm parameters
        paytm_params = {
            "MID": settings.PAYTM_MERCHANT_ID,
            "ORDER_ID": order_id,
            "CUST_ID": str(request.user.id),
            "TXN_AMOUNT": str(amount),
            "CHANNEL_ID": settings.PAYTM_CHANNEL_ID,
            "WEBSITE": settings.PAYTM_WEBSITE,
            "INDUSTRY_TYPE_ID": settings.PAYTM_INDUSTRY_TYPE_ID,
            "CALLBACK_URL": settings.PAYTM_CALLBACK_URL,
        }

        # Generate checksum hash
        paytm_params["CHECKSUMHASH"] = generateSignature(paytm_params, settings.PAYTM_MERCHANT_KEY)

        return render(request, "paytm_redirect.html", {"paytm_params": paytm_params})

    return redirect("cart")  # Redirect to cart if GET request


@csrf_exempt
def paytm_response(request):
    received_data = dict(request.POST)
    paytm_checksum = received_data.pop("CHECKSUMHASH", None)[0]
    
    is_valid_checksum = verifySignature(received_data, settings.PAYTM_MERCHANT_KEY, paytm_checksum)
    
    if is_valid_checksum:
        if received_data["STATUS"][0] == "TXN_SUCCESS":
            return render(request, "payment_success.html", {"data": received_data})
        else:
            return render(request, "payment_failed.html", {"data": received_data})
    else:
        return render(request, "payment_failed.html", {"data": "Checksum Mismatch! Payment Failed."})



def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('feedback_success')  # Redirect after submission
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})

def feedback_success(request):
    return render(request, 'feedback_success.html')  # A simple success message


from ai_agent.agent import run_ecommerce_support
from ai_agent.email_service import send_support_resolution_email
from django.http import JsonResponse

def ai_support_view(request):
    """
    Renders the Autonomous AI Customer Support Portal and processes incoming tickets.
    """
    user_orders = []
    recent_tickets = []
    
    if request.user.is_authenticated:
        user_orders = Order.objects.filter(user=request.user).order_by('-id')[:10]
        recent_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')[:5]

    ticket_result = None
    email_status = False

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        order_id = request.POST.get('order_id', '').strip()

        # Fallbacks for authenticated users if empty
        if not name and request.user.is_authenticated:
            name = request.user.get_full_name() or request.user.username
        if not email and request.user.is_authenticated:
            email = request.user.email

        if subject and message:
            # 1. Run Autonomous AI Support Agent
            ticket_result = run_ecommerce_support(
                name=name,
                email=email,
                subject=subject,
                message=message,
                order_id=order_id,
                user=request.user if request.user.is_authenticated else None
            )

            # 2. Dispatch Resolution Email to Customer
            email_status = send_support_resolution_email(
                to_email=email,
                customer_name=name,
                ticket_id=ticket_result["ticket_id"],
                subject=subject,
                resolution_text=ticket_result["ai_response"],
                order_id=ticket_result.get("order_id")
            )

            # 3. Save ticket to database for tracking
            SupportTicket.objects.create(
                ticket_id=ticket_result["ticket_id"],
                user=request.user if request.user.is_authenticated else None,
                order_id=ticket_result.get("order_id") or "",
                name=name,
                email=email,
                subject=subject,
                message=message,
                category=ticket_result.get("category"),
                urgency=ticket_result.get("urgency"),
                sentiment=ticket_result.get("sentiment"),
                action=ticket_result.get("action"),
                ai_response=ticket_result.get("ai_response"),
                status=ticket_result.get("status"),
                email_sent=email_status
            )

            # Refresh recent tickets
            if request.user.is_authenticated:
                recent_tickets = SupportTicket.objects.filter(user=request.user).order_by('-created_at')[:5]

            # If AJAX request, return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
                return JsonResponse({
                    "success": True,
                    "ticket": ticket_result,
                    "email_sent": email_status
                })

    return render(request, 'ai_support.html', {
        'user_orders': user_orders,
        'recent_tickets': recent_tickets,
        'ticket_result': ticket_result,
        'email_sent': email_status
    })

def ticket_detail_view(request, ticket_id):
    """
    Shows public or customer status of an individual support ticket.
    """
    ticket = SupportTicket.objects.filter(ticket_id=ticket_id).first()
    if not ticket:
        return redirect('ai_support')
    return render(request, 'ticket_detail.html', {'ticket': ticket})




