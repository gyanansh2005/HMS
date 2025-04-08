from django.shortcuts import render
from app2.models import Form
from datetime import date

# Create your views here.
def index(request):
    show=Form.objects.all()
    return render(request,'index.html',{'show':show})

def admin_form(request):
    if request.method == "POST":
        name = request.POST.get("name")
        date = request.POST.get("date")
        time = request.POST.get("time")
        venue = request.POST.get("venue")
        form = Form(name=name, date=date, time=time, venue=venue)
        form.save()
        show = Form.objects.all()
        return render(request, 'admin_form.html', {'show': show})
    return render(request, 'admin_form.html')


def events(request):
    today = date.today()
    upcoming_events = Form.objects.filter(date__gte=today).order_by('date')
    past_events = Form.objects.filter(date__lt=today).order_by('-date')
    
    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    }
    return render(request, 'events.html', context)