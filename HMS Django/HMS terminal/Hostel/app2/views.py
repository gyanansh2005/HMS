from django.shortcuts import render,redirect
from app2.models import Form
from datetime import date

# Create your views here.
def index(request):
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
            form = Form(name=name, date=event_date, time=time, venue=venue,description=description)
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
