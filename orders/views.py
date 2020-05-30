import smtplib
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.urls import reverse
import stripe
import os

stripe.api_key = os.getenv("Secret_Key")

from .models import (
    Pizza,
    Topping,
    Sub,
    Pasta,
    Salad,
    Dinner_Platter,
    Order,
    Cart,
    Extra,
)
from django.contrib import messages
from django.core import serializers

# Create your views here.

def home(request):
    #context = {}    
    #accounts = Account.objects.all()
    #context['accounts'] = accounts
    return render(request, "orders/home.html")
    
def index(request):
    """ Redirect to Home page if user is logged in or else to Login page"""
    # Ensure if user is logged in
    if not request.user.is_authenticated:
        return render(request, "orders/login.html", {"message": None})
    # Render index.html page

    context = {
        "user": request.user,
        "pizzas": Pizza.objects.all(),
        "toppings": Topping.objects.values("name"),
        "subs": Sub.objects.all(),
        "extras": Extra.objects.all(),
        "pastas": Pasta.objects.all(),
        "salads": Salad.objects.all(),
        "dinner_platters": Dinner_Platter.objects.all(),
    }
    # Special Pizza
    special = "Pepperoni, Spinach, Ham, Onions"
    context["special"] = special
    # Ensure order is Pending, if not then initiate
    try:
        order = Order.objects.get(user=request.user, status="Pending")
    except:
        order = Order(user=request.user)
        order.save()
    cart = Cart.objects.filter(user=request.user, order_id=order.pk)
    count = 0
    for item in cart:
        count += 1
    context["count"] = count
    # Render index.html page
    return render(request, "orders/index.html", context)



def register_view(request):
    """ Register user """
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get form fields
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        username = request.POST["username"]
        password = request.POST["password"]
        password2 = request.POST["password"]
        # Ensure email is unique
        user = User.objects.filter(email=email)
        if len(user) != 0:
            return render(
                request, "orders/register.html", {"message": "E-mail already exists!"}
            )
        # Ensure username is unique
        user = User.objects.filter(username=username)
        if len(user) != 0:
            return render(
                request, "orders/register.html", {"message": "Username already exists!"}
            )
        # Add user to DB and save it
        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password,
        )
        user.save()
        # Redirect user to login page
        return render(request, "orders/login.html", {"message": "Account created!"})
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render(request, "orders/register.html")



def login_view(request):
    """ Log user in """
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Get username and password
        username = request.POST["username"]
        password = request.POST["password"]
        # Authenticate
        user = authenticate(request, username=username, password=password)
        # Ensure if authentication is successful
        if user is not None:
            # Log in user and redirect to index
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(
                request, "orders/login.html", {"message": "Invalid username/password!"}
            )
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render(request, "orders/login.html", {"message": None})


def logout_view(request):
    """ Log user out """
    # Log user out
    logout(request)
    # Render login page once logged out
    return render(request, "orders/login.html", {"message": "Logged out."})


def add_item_view(request):
    """ Review item """
    # Get form fields
    name = request.POST["name"]
    item_price = float(request.POST["item_price"])
    size = request.POST["size"]
    # Try to get special pizza's toppings
    try:
        special = request.POST["special"]
    except:
        special = ""
    # Generate extras name
    extras = special
    # Ensure toppings/extras for pizzas/subs are selected
    try:
        extra1 = request.POST["extra1"]
    except:
        extra1 = ""
    try:
        extra2 = request.POST["extra2"]
    except:
        extra2 = ""
    try:
        extra3 = request.POST["extra3"]
    except:
        extra3 = ""
    try:
        extra4 = request.POST["extra4"]
    except:
        extra4 = ""
    # Generate extra items name
    if len(extra1) != 0:
        extras += f"{extra1},"
    if len(extra2) != 0:
        extras += f"{extra2},"
    if len(extra3) != 0:
        extras += f"{extra3},"
    if len(extra4) != 0:
        extras += f"{extra4}"
    length = len(extras)
    try:
        if extras[length - 1] == ",":
            extras = extras[:-1]
    except:
        extras = ""
    extras = extras.replace(",", ", ")
    # Get extra price for subs
    try:
        price1 = float(request.POST["price1"])
    except:
        price1 = 0.00
    try:
        price2 = float(request.POST["price2"])
    except:
        price2 = 0.00
    try:
        price3 = float(request.POST["price3"])
    except:
        price3 = 0.00
    try:
        price4 = float(request.POST["price4"])
    except:
        price4 = 0.00
    # Calculate total extra price
    extra_price = price1 + price2 + price3 + price4
    # Add extra price to item price
    item_price += extra_price
    # Generate cart item name
    cart_item = name
    if len(size) != 0:
        cart_item += f" ({size})"
    # Getting logged in user
    user = request.user
    # Get latest Pending order
    order = Order.objects.get(user=user, status="Pending")
    # Get order id
    order_id = order.id
    # Add item in cart and save it
    cart = Cart(
        user=user,
        order_id=order_id,
        cart_item=cart_item,
        extras=extras,
        item_price=item_price,
    )
    cart.save()
    # Increment order_total with item price
    order.order_total = float(order.order_total) + item_price
    order.save()
    # Redirect user to index with a message
    messages.success(request, "Item added to Cart!")
    return HttpResponseRedirect(reverse("index"))


def remove_item_view(request):
    """ Removes Pizza from cart """
    # Get data from form fields
    item_id = request.POST["item_id"]
    item_price = request.POST["item_price"]
    # Getting logged in user
    user = request.user
    # Remove item from cart
    cart = Cart.objects.filter(id=item_id).delete()
    # Decrement order_total with item price
    order = Order.objects.get(user=user, status="Pending")
    order.order_total = float(order.order_total) - float(item_price)
    order.save()
    # Redirect user to cart
    messages.success(request, "Item removed from Card!")
    return HttpResponseRedirect(reverse("cart"))


def cart_view(request):
    """ Displays cart and removes items from cart """
    # Get initialized order
    order = Order.objects.get(user=request.user, status="Pending")
    # Get cart items
    cart = Cart.objects.filter(user=request.user, order_id=order.pk)
    # Count cart items
    count = 0
    for item in cart:
        count += 1
    # Pass cart items to cart.html
    context = {
        "cart": cart,
        "count": count,
        "order_total": order.order_total,
        "order_id": order.id,
    }
    return render(request, "orders/cart.html", context)


def place_order_view(request):
    """ Places and completes an order and sends an email to the user """
    # Get order id
    order_id = request.POST["order_id"]
    # Get order object of user
    order = Order.objects.get(user=request.user, status="Pending")
    # Get items
    cart = Cart.objects.filter(user=request.user, order_id=order.pk).all()     
        
    # Change order status to completed and save it
    order.status = "Completed"
    order.save()
    
    """ Send mail (Personal touch) """
    # Sender & receiver email
    sender = "testingtauhidproject3@gmail.com"
    request.user.email
    receiver = request.user.email
    # Message to be sent
    message = f"""
    Your order has been placed successfully!
    You ordered:

        """
    for item in cart:
        message += f"""{item.cart_item}: ${item.item_price}
        """
        if item.extras != "":
            message += f"""({item.extras})
        """
        message += """
        """
    message += f"""
    Your order total: ${order.order_total}
    
    Thanks for visiting us! We hope you have a good day!
    Oh, and always remember:
    Eat More Pizza!
    """
    #send mail
    send_mail('Hello order message', message, sender, ['testingtauhidproject3@gmail.com', 'tauhidmy11@gmail.com'])
    # Redirect user to index
    messages.success(request, "Order has been placed!")
    return HttpResponseRedirect(reverse("index"))
  
def order1(request):

    return render(request, 'orders/order1.html')
    
def charge(request):
    # Get current order 
    order = Order.objects.get(user=request.user, status="Pending")

    # Get the total for the order, so we know what to charge
    #total = Order.objects.filter(order=current_order).aggregate(Sum('order_total'))['price__sum']

    # Grab the form info for Stripe charge
    # Creating Charges on Server side:  https://stripe.com/docs/charges
    token = request.POST.get('stripeToken')
    charge = stripe.Charge.create(
        amount=int(order.order_total * 100),   # this is in cents
        currency='usd',
        description='Pizza Order',
        source=token,
    )

    # Don't change the cart status to placed until after the charge went through
    order.state = "placed"
    #current_order.save()
    #order.order_total = float(order.order_total) + item_price
    order.save()

     
 
    return render(request, "orders/success.html")


def successMsg(request, args):
	order_total = args
	return render(request, 'orders/success.html', {'order_total':order_total}, context)
    
def status(request):
    orders = Order.objects.all()
    customers = User.objects.all()
    total_customers = customers.count()
    total_orders = orders.count()
    Completed = orders.filter(status='Completed').count()
    pending = orders.filter(status='Pending').count()

    context= {'orders':orders, 'customers':customers, 'total_customers': total_customers,
    'total_orders':total_orders, 'Completed':Completed, 'pending': pending}

    return render(request, 'orders/status.html', context)

def gen_status(request):
    orders = Order.objects.all()
    customers = User.objects.all()
    total_customers = customers.count()
    total_orders = orders.count()
    Completed = orders.filter(status='Completed').count()
    pending = orders.filter(status='Pending').count()

    context= {'orders':orders, 'customers':customers, 'total_customers': total_customers,
    'total_orders':total_orders, 'Completed':Completed, 'pending': pending}

    return render(request, 'orders/gen_status.html', context)

def show_order_view(request):
    """ Displays a list of orders to admin """
    # Get orders and cart items for each order
    context = {
        "orders": Order.objects.all().filter(status="Completed"),
        "cart": Cart.objects.all(),
    }
    # Count cart items and add it to context
    order = Order.objects.get(user=request.user, status="Pending")
    cart = Cart.objects.filter(user=request.user, order_id=order.pk)
    count = 0
    for item in cart:
        count += 1
    context["count"] = count
    # Render orders.html page
    return render(request, "orders/orders.html", context)
 


 #delete order
def deleteOrder(request, pk):
    order = Order.objects.get(id=pk)
    if request.method == "POST":
        order.delete()
        return render(request, "orders/status.html")

    context = {'item':order}
    return render(request, 'orders/delete.html', context )
