from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from app2.models import Form
from datetime import date
from django.contrib import messages
from .models import MessMenu, MessRules, TodayMenu
from django.db.models import Q

def app2index(request):
    show = Form.objects.all()
    return render(request, 'index.html', {'show': show})

def base(request):
    return render(request, 'base.html')

def admin_form(request):
    try:
        if request.method == "POST":
            name = request.POST.get("name")
            event_date = request.POST.get("date")
            time = request.POST.get("time")
            venue = request.POST.get("venue")
            description = request.POST.get('description')
            organizer = request.POST.get('organizer')

            form = Form(name=name, date=event_date, time=time, venue=venue, description=description, organizer=organizer)
            form.save()
        
        today = date.today()
        upcoming_events = Form.objects.filter(date__gte=today).order_by('date')
        past_events = Form.objects.filter(date__lt=today).order_by('-date')

    except Exception as e:
        print("Error:", e)
        upcoming_events = []
        past_events = []

    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'admin_form.html', context)

def delete(request, id):
    data = Form.objects.get(id=id) 
    data.delete()
    return redirect('admin_form')

def update(request, id):
    data = Form.objects.get(id=id)
    if request.method == "POST":
        data.name = request.POST.get("name")
        data.date = request.POST.get("date")
        data.time = request.POST.get("time")
        data.venue = request.POST.get("venue")
        data.description = request.POST.get('description')
        data.organizer = request.POST.get('organizer')
        data.save()
        return redirect('admin_form')  
    return render(request, 'update.html', {'data': data})

def events(request):
    today = date.today()
    upcoming_events = Form.objects.filter(date__gte=today).order_by('date')
    past_events = Form.objects.filter(date__lt=today).order_by('-date')
    
    featured_event = upcoming_events.first()

    context = {
        'featured_event': featured_event,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'events.html', context)

def mess(request):
    today = date(2025, 4, 12)  # Current date
    today_day = today.strftime("%A")  # "Saturday"
    
    # Fetch or create today's menu from MessMenu
    today_menu = TodayMenu.objects.filter(day=today_day).order_by('-created_at').first()
    if not today_menu:
        # If no TodayMenu exists, try to set it from MessMenu
        mess_menu = MessMenu.objects.filter(day=today_day).first()
        if mess_menu:
            today_menu = TodayMenu.objects.create(
                day=mess_menu.day,
                meal_type=mess_menu.meal_type,
                menu=mess_menu.menu
            )
    
    # Fetch weekly menu
    menus = MessMenu.objects.all()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Handle day filter
    day_filter = request.GET.get('day', '').capitalize()
    if day_filter in days:
        menus = menus.filter(day=day_filter)
    else:
        # Default to today's menu if no filter
        menus = menus.filter(day=today_day)

    # Fetch mess rules
    rules = MessRules.objects.all()
    
    context = {
        'today_menu': today_menu,
        'menus': menus,
        'days': days,
        'day_filter': day_filter.lower() if day_filter else '',
        'rules': rules,
    }
    return render(request, 'mess.html', context)


from django.shortcuts import render, redirect
from app2.models import Form
from datetime import date
from django.contrib import messages
from .models import MessMenu, MessRules, TodayMenu
from django.db.models import Q

# ... (existing views remain the same)

def set_today_menu(request, menu_id):
    menu = MessMenu.objects.get(id=menu_id)
    TodayMenu.objects.update_or_create(
        day=menu.day,
        defaults={'meal_type': menu.meal_type, 'menu': menu.menu}
    )
    messages.success(request, f"Menu set for {menu.day} as today's menu.")
    return redirect('mess')

def update_mess_menu(request, menu_id):
    menu = MessMenu.objects.get(id=menu_id)
    if request.method == "POST":
        form = MessMenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu updated successfully.")
            return redirect('mess')
    else:
        form = MessMenuForm(instance=menu)
    return render(request, 'update_mess_menu.html', {'form': form})

def delete_mess_menu(request, menu_id):
    menu = MessMenu.objects.get(id=menu_id)
    if request.method == "POST":
        menu.delete()
        messages.success(request, "Menu deleted successfully.")
        return redirect('mess')
    return render(request, 'confirm_delete.html', {'menu': menu})





# app2/views.py
from django.shortcuts import render, redirect
from .models import DiscussionMessage
from .forms import DiscussionForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@login_required
def discussion_center(request):
    if request.method == 'POST':
        form = DiscussionForm(request.POST)
        if form.is_valid():
            DiscussionMessage.objects.create(
                user=request.user,
                message=form.cleaned_data['message'],
                is_notification=False
            )
            return redirect('discussion_center')
    
    messages = DiscussionMessage.objects.all().order_by('-timestamp')[:50]
    return render(request, 'discussion.html', {
        'chat_messages': messages,
        'form': DiscussionForm()
    })
    
@require_POST
@login_required
def delete_notification(request, msg_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    message = get_object_or_404(DiscussionMessage, id=msg_id)
    message.delete()
    return redirect('admin_dashboard')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import LostItem, FoundItem, ClaimRequest
from .forms import LostItemForm, FoundItemForm, ClaimRequestForm

def home(request):
    return render(request, 'home.html')  # Adjusted path

def report_lost_item(request):
    if request.method == 'POST':
        form = LostItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user  # Assumes user still needed
            item.save()
            messages.success(request, 'Lost item reported successfully!')
            return redirect('lost_items')
    else:
        form = LostItemForm()
    return render(request, 'report_lost.html', {'form': form})  # Adjusted path

def report_found_item(request):
    if request.method == 'POST':
        form = FoundItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user  # Assumes user still needed
            item.save()
            messages.success(request, 'Found item reported successfully!')
            return redirect('found_items')
    else:
        form = FoundItemForm()
    return render(request, 'report_found.html', {'form': form})  # Adjusted path

def lost_items(request):
    items = LostItem.objects.filter(is_claimed=False)
    query = request.GET.get('q')
    category = request.GET.get('category')

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    if category:
        items = items.filter(category=category)

    return render(request, 'lost_items.html', {
        'items': items,
        'query': query,
        'category': category
    })  # Adjusted path

def found_items(request):
    items = FoundItem.objects.filter(is_claimed=False)
    query = request.GET.get('q')
    category = request.GET.get('category')

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )

    if category:
        items = items.filter(category=category)

    return render(request, 'found_items.html', {
        'items': items,
        'query': query,
        'category': category
    })  # Adjusted path

def claim_item(request, item_id):
    item = get_object_or_404(FoundItem, id=item_id)

    if request.method == 'POST':
        form = ClaimRequestForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.item = item
            claim.user = request.user  # Assumes user still needed
            claim.save()
            messages.success(request, 'Claim request submitted successfully!')
            return redirect('found_items')
    else:
        form = ClaimRequestForm()

    return render(request, 'claim_item.html', {
        'form': form,
        'item': item
    })  # Adjusted path

def manage_claims(request):
    claims = ClaimRequest.objects.filter(is_approved=False)
    return render(request, 'manage_claims.html', {'claims': claims})  # Adjusted path

def approve_claim(request, claim_id):
    claim = get_object_or_404(ClaimRequest, id=claim_id)
    claim.is_approved = True
    claim.item.is_claimed = True
    claim.item.save()
    claim.save()
    messages.success(request, 'Claim approved successfully!')
    return redirect('manage_claims')  # Adjusted path