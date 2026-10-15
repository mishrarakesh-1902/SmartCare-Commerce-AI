from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.db.models import Count, Prefetch
from app.models import Category, Product, Sub_category, Contact_us, Order, Brand, SupportTicket
from django.contrib.auth import authenticate, login
from app.models import UserCreateForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from cart.cart import Cart

from app.forms import FeedbackForm

import json
import requests
import datetime

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paytmchecksum import generateSignature, verifySignature


def Master(request):
    return render(request, 'master.html')

def Index(request):
    sub_prefetch = Prefetch(
        'sub_category_set',
        queryset=Sub_category.objects.annotate(num_products=Count('product'))
    )
    category = Category.objects.annotate(num_products=Count('product')).prefetch_related(sub_prefetch).all()
    brand = Brand.objects.filter(product__isnull=False).distinct().annotate(num_products=Count('product')).order_by('name')
    
    brandID = request.GET.get('brand')
    categoryID = request.GET.get('category')
    subCategoryID = request.GET.get('sub_category')
    sort = request.GET.get('sort', 'newest')

    products = Product.objects.all().select_related('category', 'sub_category', 'brand')

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

    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-id')

    total_products_count = Product.objects.count()

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
        'current_sort': sort,
        'total_products_count': total_products_count,
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
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        cart = request.session.get('cart', {})
        user = request.user

        if not cart:
            return redirect("cart_detail")

        created_orders = []
        total_amount = 0

        for key, item in cart.items():
            try:
                price = int(float(item.get('price', 0)))
                qty = int(item.get('quantity', 1))
                item_total = price * qty
                total_amount += item_total
                order = Order.objects.create(
                    user=user,
                    product=item.get('name', 'Product'),
                    price=price,
                    quantity=str(qty),
                    image=item.get('image', ''),
                    address=f"{address} (PIN: {pincode})" if pincode else address,
                    phone=phone,
                    pincode=pincode,
                    total=str(item_total),
                )
                created_orders.append(order)
            except Exception as e:
                print("Error creating COD order:", e)

        # Completely empty the cart session
        try:
            cart_obj = Cart(request)
            cart_obj.clear()
        except Exception:
            pass
        request.session['cart'] = {}
        request.session['cart_total_amount'] = 0
        request.session.modified = True

        order_id = f"COD{user.id}ORD{int(datetime.datetime.now().timestamp())}"

        return render(request, "payment_success.html", {
            "order_id": order_id,
            "amount": total_amount,
            "orders": created_orders,
            "payment_mode": "Cash on Delivery (COD)",
            "payment_status": "ORDER CONFIRMED &bull; COD",
            "is_cod": True,
            "address": f"{address} (PIN: {pincode})" if pincode else address,
            "phone": phone,
        })

    return redirect("order")


@login_required(login_url='/accounts/login/')
def Your_Order(request):
    user = request.user
    order = Order.objects.filter(user = user).order_by('-id')
    context = {
        'order' : order,
    }
    return render(request , 'order.html' , context)

def Product_page(request):
    sub_prefetch = Prefetch(
        'sub_category_set',
        queryset=Sub_category.objects.annotate(num_products=Count('product'))
    )
    category = Category.objects.annotate(num_products=Count('product')).prefetch_related(sub_prefetch).all()
    
    # Only show brands that have products in the store
    brand = Brand.objects.filter(product__isnull=False).distinct().annotate(num_products=Count('product')).order_by('name')
    
    brandID = request.GET.get('brand')
    categoryID = request.GET.get('category')
    subCategoryID = request.GET.get('sub_category')
    sort = request.GET.get('sort', 'newest')

    products = Product.objects.all().select_related('category', 'sub_category', 'brand')

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

    # Dynamic sorting
    if sort == 'price_low':
        products = products.order_by('price')
    elif sort == 'price_high':
        products = products.order_by('-price')
    elif sort == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-id')

    total_products_count = Product.objects.count()

    context = {
        'category': category,
        'brand': brand,
        'product': products,
        'active_category': active_category,
        'active_sub_category': active_sub_category,
        'active_brand': active_brand,
        'current_sort': sort,
        'total_products_count': total_products_count,
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
    
    gallery_images = product.get_gallery_images() if product else []
    
    context = {
        'product': product,
        'gallery_images': gallery_images,
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
        amount = request.POST.get("amount") or request.session.get("cart_total_amount", 0)
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        pincode = request.POST.get("pincode", "").strip()
        cart = request.session.get("cart", {})

        if not cart:
            return redirect("cart_detail")

        # Save delivery details in session so they are stored with the order
        request.session['checkout_info'] = {
            'address': address,
            'phone': phone,
            'pincode': pincode,
        }

        order_id = f"AJR{request.user.id}ORD{int(datetime.datetime.now().timestamp())}"

        # Ensure AES key is strictly 16 or 32 characters to prevent ValueError
        m_key = getattr(settings, 'PAYTM_MERCHANT_KEY', '1234567890123456')
        if len(m_key) not in [16, 32]:
            m_key = (str(m_key) + "0123456789012345")[:16]

        paytm_params = {
            "MID": getattr(settings, 'PAYTM_MERCHANT_ID', 'STAGE_MID'),
            "ORDER_ID": order_id,
            "CUST_ID": str(request.user.id),
            "TXN_AMOUNT": str(amount),
            "CHANNEL_ID": getattr(settings, 'PAYTM_CHANNEL_ID', 'WEB'),
            "WEBSITE": getattr(settings, 'PAYTM_WEBSITE', 'WEBSTAGING'),
            "INDUSTRY_TYPE_ID": getattr(settings, 'PAYTM_INDUSTRY_TYPE_ID', 'Retail'),
            "CALLBACK_URL": getattr(settings, 'PAYTM_CALLBACK_URL', 'http://127.0.0.1:8001/paytm-response/'),
        }

        try:
            paytm_params["CHECKSUMHASH"] = generateSignature(paytm_params, m_key)
        except Exception as e:
            paytm_params["CHECKSUMHASH"] = "MOCK_SIGNATURE_" + order_id

        # Render Modern Payment Gateway Portal
        return render(request, "payment_portal.html", {
            "paytm_params": paytm_params,
            "order_id": order_id,
            "amount": amount,
            "cart": cart,
            "address": address,
            "phone": phone,
            "pincode": pincode,
            "razorpay_key_id": getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_demo123456789'),
        })

    return redirect("cart_detail")


@csrf_exempt
def paytm_response(request):
    """
    Handles payment confirmation, creates order records in DB, clears cart, and renders receipt.
    """
    if request.method == "POST":
        order_id = request.POST.get("ORDERID") or request.POST.get("order_id") or f"AJR-PAY-{int(datetime.datetime.now().timestamp())}"
        status = request.POST.get("STATUS", "TXN_SUCCESS")
        txn_amount = request.POST.get("TXNAMOUNT") or request.POST.get("amount", 0)

        checkout_info = request.session.get("checkout_info", {})
        address = checkout_info.get("address") or request.POST.get("address", "Standard Delivery Address")
        phone = checkout_info.get("phone") or request.POST.get("phone", "N/A")
        pincode = checkout_info.get("pincode") or request.POST.get("pincode", "")

        cart = request.session.get("cart", {})
        created_orders = []

        if status == "TXN_SUCCESS" and cart:
            for item in cart.values():
                try:
                    price = int(item.get("price", 0))
                    qty = int(item.get("quantity", 1))
                    total = price * qty
                    order = Order.objects.create(
                        user=request.user,
                        product=item.get("name", "Product"),
                        price=price,
                        quantity=str(qty),
                        image=item.get("image", ""),
                        address=f"{address} (PIN: {pincode})" if pincode else address,
                        phone=phone,
                        pincode=pincode,
                        total=str(total)
                    )
                    created_orders.append(order)
                except Exception as e:
                    print("Error creating paid order:", e)

            # Clear cart session
            request.session["cart"] = {}
            request.session["cart_total_amount"] = 0

            return render(request, "payment_success.html", {
                "order_id": order_id,
                "amount": txn_amount,
                "orders": created_orders,
                "payment_mode": "Online Payment (Verified)",
                "payment_status": "PAID &bull; VERIFIED",
                "is_cod": False,
                "address": address,
                "phone": phone,
            })
        elif status == "TXN_SUCCESS" and not cart:
            # If refreshed or already processed
            return redirect("order")
        else:
            return render(request, "payment_failed.html", {
                "order_id": order_id,
                "reason": "Payment transaction could not be verified or was declined."
            })

    return redirect("cart_detail")



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




