from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from store.models import Product, Variation
from .models import Cart, CartItem

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []

    if request.method == 'POST':
        for key in request.POST:
            value = request.POST[key]
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variation.append(variation)
            except Variation.DoesNotExist:
                pass

    # ✅ Correctly unpack cart from get_or_create
    cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))

    # ✅ Check for existing cart items
    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
    if is_cart_item_exists:
        cart_items = CartItem.objects.filter(product=product, cart=cart)
        for item in cart_items:
            existing_variation = list(item.variation.all())
            if set(existing_variation) == set(product_variation):
                item.quantity += 1
                item.save()
                break
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if product_variation:
                cart_item.variation.set(product_variation)
            cart_item.save()
    else:
        cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
        if product_variation:
            cart_item.variation.set(product_variation)
        cart_item.save()

    return redirect('cart')

def remove_cart(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart__cart_id=_cart_id(request))
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')


def remove_cart_item(request, cart_item_id):
    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart__cart_id=_cart_id(request))
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_items=None):
    tax = grand_total = 0
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            total += item.sub_total()
            quantity += item.quantity
        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total
    }
    return render(request, 'store/cart.html', context)
