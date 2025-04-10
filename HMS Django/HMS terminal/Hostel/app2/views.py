from django.shortcuts import render,redirect
from app2.models import Form
from datetime import date
from django.contrib import messages
from .models import MessMenu, TodayMenu


# Create your views here.
def app2index(request):
    show=Form.objects.all()
    return render(request,'index.html',{'show':show})

def base(request):
    return render(request,'base.html')

def admin_form(request):
    try:
        if request.method == "POST":
            name = request.POST.get("name")
            event_date = request.POST.get("date")
            time = request.POST.get("time")
            venue = request.POST.get("venue")
            description = request.POST.get('description')
            organizer = request.POST.get('organizer')  # <- Fetching from the form

            form = Form(name=name, date=event_date, time=time, venue=venue,description=description,organizer=organizer)
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
    
    featured_event = upcoming_events.first()  # 👈 this will be shown in the hero section

    context = {
        'featured_event': featured_event,
        'upcoming_events': upcoming_events,  # exclude the featured one from list
        'past_events': past_events,
    }
    return render(request, 'events.html', context)

from .models import MessMenu
from datetime import datetime

from .models import MessMenu, TodayMenu
from datetime import datetime

def mess(request):
    today = datetime.now().strftime("%A")
    menu_items = MessMenu.objects.all()
    today_menu = TodayMenu.objects.all()  # 🔁 This line is updated

    context = {
        'menu_items': menu_items,
        'today_menu': today_menu,
        'days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        'meals': ["Breakfast", "Lunch", "Dinner"],
        'mess_timings': {
            "Breakfast": "7:00 AM - 9:00 AM",
            "Lunch": "12:30 PM - 2:00 PM",
            "Dinner": "7:30 PM - 9:00 PM",
        },
    }

    return render(request, 'mess.html', context)


def mess_admin(request):
    if request.method == 'POST':
        day = request.POST.get('day')
        meal_type = request.POST.get('meal_type')
        menu = request.POST.get('menu')

        MessMenu.objects.create(
            day=day,
            meal_type=meal_type,
            menu=menu
        )

        messages.success(request, "Menu added successfully!")
        return redirect('mess_admin')
    
    # ✅ Fetch all menus to display
    menus = MessMenu.objects.all()

    return render(request, 'mess_admin.html', {'menus': menus})


from .models import MessMenu
from django.contrib import messages

# 🔁 UPDATE menu
def update_mess_menu(request, id):
    menu_item = MessMenu.objects.get(id=id)
    if request.method == 'POST':
        menu_item.day = request.POST.get('day')
        menu_item.meal_type = request.POST.get('meal_type')
        menu_item.menu = request.POST.get('menu')
        menu_item.save()
        messages.success(request, "Menu updated successfully!")
        return redirect('mess_admin')

    return render(request, 'update_mess_menu.html', {'menu_item': menu_item})

# ❌ DELETE menu
def delete_mess_menu(request, id):
    menu_item = MessMenu.objects.get(id=id)
    menu_item.delete()
    messages.success(request, "Menu deleted successfully!")
    return redirect('mess_admin')


from .models import MessMenu, TodayMenu

def set_today_menu(request, id):
    if request.method == 'POST':
        try:
            menu = MessMenu.objects.get(id=id)

            # Clear previous entry (if you want only one today’s menu)
            TodayMenu.objects.all().delete()

            # Save new today menu
            TodayMenu.objects.create(
                day=menu.day,
                meal_type=menu.meal_type,
                menu=menu.menu
            )

            messages.success(request, "Today's menu updated successfully!")
        except MessMenu.DoesNotExist:
            messages.error(request, "Menu item not found!")

    return redirect('mess_admin')
