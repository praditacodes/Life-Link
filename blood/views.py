from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum,Q
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta, datetime
from django.core.mail import send_mail
from django.contrib.auth.models import User
from donor import models as dmodels
from patient import models as pmodels
from donor import forms as dforms
from patient import forms as pforms
from django.contrib.auth import logout, login, authenticate, update_session_auth_hash
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from django.contrib import messages
from .utils import generate_otp, send_otp_via_sms, is_otp_valid
from .forms import OTPVerificationForm, PhoneNumberForm, PasswordResetForm, ChangePasswordForm
from .models import CustomUser
from phonenumber_field.phonenumber import to_python


def logout_view(request):
    logout(request)
    return redirect('')

def home_view(request):
    x=models.Stock.objects.all()
    print(x)
    if len(x)==0:
        blood1=models.Stock()
        blood1.bloodgroup="A+"
        blood1.save()

        blood2=models.Stock()
        blood2.bloodgroup="A-"
        blood2.save()

        blood3=models.Stock()
        blood3.bloodgroup="B+"
        blood3.save()        

        blood4=models.Stock()
        blood4.bloodgroup="B-"
        blood4.save()

        blood5=models.Stock()
        blood5.bloodgroup="AB+"
        blood5.save()

        blood6=models.Stock()
        blood6.bloodgroup="AB-"
        blood6.save()

        blood7=models.Stock()
        blood7.bloodgroup="O+"
        blood7.save()

        blood8=models.Stock()
        blood8.bloodgroup="O-"
        blood8.save()

    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')  
    return render(request,'blood/index.html')

def is_donor(user):
    return user.groups.filter(name='DONOR').exists()

def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


def afterlogin_view(request):
    if is_donor(request.user):      
        return redirect('donor/donor-dashboard')
                
    elif is_patient(request.user):
        return redirect('patient/patient-dashboard')
    else:
        return redirect('admin-dashboard')

@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    totalunit=models.Stock.objects.aggregate(Sum('unit'))
    dict={

        'A1':models.Stock.objects.get(bloodgroup="A+"),
        'A2':models.Stock.objects.get(bloodgroup="A-"),
        'B1':models.Stock.objects.get(bloodgroup="B+"),
        'B2':models.Stock.objects.get(bloodgroup="B-"),
        'AB1':models.Stock.objects.get(bloodgroup="AB+"),
        'AB2':models.Stock.objects.get(bloodgroup="AB-"),
        'O1':models.Stock.objects.get(bloodgroup="O+"),
        'O2':models.Stock.objects.get(bloodgroup="O-"),
        'totaldonors':dmodels.Donor.objects.all().count(),
        'totalbloodunit':totalunit['unit__sum'],
        'totalrequest':models.BloodRequest.objects.all().count(),
        'totalapprovedrequest':models.BloodRequest.objects.all().filter(status='Approved').count()
    }
    return render(request,'blood/admin_dashboard.html',context=dict)

@login_required(login_url='adminlogin')
def admin_blood_view(request):
    dict={
        'bloodForm':forms.BloodForm(),
        'A1':models.Stock.objects.get(bloodgroup="A+"),
        'A2':models.Stock.objects.get(bloodgroup="A-"),
        'B1':models.Stock.objects.get(bloodgroup="B+"),
        'B2':models.Stock.objects.get(bloodgroup="B-"),
        'AB1':models.Stock.objects.get(bloodgroup="AB+"),
        'AB2':models.Stock.objects.get(bloodgroup="AB-"),
        'O1':models.Stock.objects.get(bloodgroup="O+"),
        'O2':models.Stock.objects.get(bloodgroup="O-"),
    }
    if request.method=='POST':
        bloodForm=forms.BloodForm(request.POST)
        if bloodForm.is_valid() :        
            bloodgroup=bloodForm.cleaned_data['bloodgroup']
            stock=models.Stock.objects.get(bloodgroup=bloodgroup)
            stock.unit=bloodForm.cleaned_data['unit']
            stock.save()
        return HttpResponseRedirect('admin-blood')
    return render(request,'blood/admin_blood.html',context=dict)


@login_required(login_url='adminlogin')
def admin_donor_view(request):
    donors=dmodels.Donor.objects.all()
    return render(request,'blood/admin_donor.html',{'donors':donors})

@login_required(login_url='adminlogin')
def update_donor_view(request,pk):
    donor=dmodels.Donor.objects.get(id=pk)
    user=dmodels.User.objects.get(id=donor.user_id)
    userForm=dforms.DonorUserForm(instance=user)
    donorForm=dforms.DonorForm(request.FILES,instance=donor)
    mydict={'userForm':userForm,'donorForm':donorForm}
    if request.method=='POST':
        userForm=dforms.DonorUserForm(request.POST,instance=user)
        donorForm=dforms.DonorForm(request.POST,request.FILES,instance=donor)
        if userForm.is_valid() and donorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            donor=donorForm.save(commit=False)
            donor.user=user
            donor.bloodgroup=donorForm.cleaned_data['bloodgroup']
            donor.save()
            return redirect('admin-donor')
    return render(request,'blood/update_donor.html',context=mydict)


@login_required(login_url='adminlogin')
def delete_donor_view(request,pk):
    donor=dmodels.Donor.objects.get(id=pk)
    user=User.objects.get(id=donor.user_id)
    user.delete()
    donor.delete()
    return HttpResponseRedirect('/admin-donor')

@login_required(login_url='adminlogin')
def admin_patient_view(request):
    patients=pmodels.Patient.objects.all()
    return render(request,'blood/admin_patient.html',{'patients':patients})


@login_required(login_url='adminlogin')
def update_patient_view(request,pk):
    patient=pmodels.Patient.objects.get(id=pk)
    user=pmodels.User.objects.get(id=patient.user_id)
    userForm=pforms.PatientUserForm(instance=user)
    patientForm=pforms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=pforms.PatientUserForm(request.POST,instance=user)
        patientForm=pforms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.user=user
            patient.bloodgroup=patientForm.cleaned_data['bloodgroup']
            patient.save()
            return redirect('admin-patient')
    return render(request,'blood/update_patient.html',context=mydict)


@login_required(login_url='adminlogin')
def delete_patient_view(request,pk):
    patient=pmodels.Patient.objects.get(id=pk)
    user=User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return HttpResponseRedirect('/admin-patient')

@login_required(login_url='adminlogin')
def admin_request_view(request):
    requests=models.BloodRequest.objects.all().filter(status='Pending')
    return render(request,'blood/admin_request.html',{'requests':requests})

@login_required(login_url='adminlogin')
def admin_request_history_view(request):
    requests=models.BloodRequest.objects.all().exclude(status='Pending')
    return render(request,'blood/admin_request_history.html',{'requests':requests})

@login_required(login_url='adminlogin')
def admin_donation_view(request):
    donations=dmodels.BloodDonate.objects.all()
    return render(request,'blood/admin_donation.html',{'donations':donations})

@login_required(login_url='adminlogin')
def update_approve_status_view(request,pk):
    req=models.BloodRequest.objects.get(id=pk)
    message=None
    bloodgroup=req.bloodgroup
    unit=req.unit
    stock=models.Stock.objects.get(bloodgroup=bloodgroup)
    if stock.unit > unit:
        stock.unit=stock.unit-unit
        stock.save()
        req.status="Approved"
        
    else:
        message="Stock Doest Not Have Enough Blood To Approve This Request, Only "+str(stock.unit)+" Unit Available"
    req.save()

    requests=models.BloodRequest.objects.all().filter(status='Pending')
    return render(request,'blood/admin_request.html',{'requests':requests,'message':message})

@login_required(login_url='adminlogin')
def update_reject_status_view(request,pk):
    req=models.BloodRequest.objects.get(id=pk)
    req.status="Rejected"
    req.save()
    return HttpResponseRedirect('/admin-request')

@login_required(login_url='adminlogin')
def approve_donation_view(request,pk):
    donation=dmodels.BloodDonate.objects.get(id=pk)
    donation_blood_group=donation.bloodgroup
    donation_blood_unit=donation.unit

    stock=models.Stock.objects.get(bloodgroup=donation_blood_group)
    stock.unit=stock.unit+donation_blood_unit
    stock.save()

    donation.status='Approved'
    donation.save()
    return HttpResponseRedirect('/admin-donation')


@login_required(login_url='adminlogin')
def reject_donation_view(request,pk):
    donation=dmodels.BloodDonate.objects.get(id=pk)
    donation.status='Rejected'
    donation.save()
    return HttpResponseRedirect('/admin-donation')

@login_required
@user_passes_test(is_patient)
def search_donors_view(request):
    donors = []
    if request.method == 'GET':
        bloodgroup = request.GET.get('bloodgroup')
        city = request.GET.get('city')
        radius = request.GET.get('radius', 10)  # Default 10km radius

        if bloodgroup and city:
            # Get coordinates for the search city
            geolocator = Nominatim(user_agent="blood_link")
            try:
                location = geolocator.geocode(city)
                if location:
                    search_coords = (location.latitude, location.longitude)
                    
                    # Get all donors with matching blood group
                    donor_list = dmodels.Donor.objects.filter(bloodgroup=bloodgroup)
                    
                    # Calculate distance for each donor
                    for donor in donor_list:
                        if donor.latitude and donor.longitude:
                            donor_coords = (float(donor.latitude), float(donor.longitude))
                            distance = geodesic(search_coords, donor_coords).kilometers
                            
                            if distance <= float(radius):
                                donor.distance = distance
                                donors.append(donor)
                    
                    # Sort donors by distance
                    donors.sort(key=lambda x: x.distance)
            except Exception as e:
                print(f"Error in geocoding: {e}")

    return render(request, 'blood/search.html', {'donors': donors})

def verify_phone(request):
    if request.method == 'POST':
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone_number = str(form.cleaned_data['phone_number'])
            phone_number = phone_number.replace(' ', '')
            user = request.user
            user.phone_number = phone_number
            user.save()
            
            # Generate and send OTP
            otp = generate_otp()
            if send_otp_via_sms(phone_number, otp):
                user.otp = otp
                user.otp_created_at = datetime.now()
                user.save()
                return redirect('verify_otp')
            else:
                messages.error(request, 'Failed to send OTP. Please try again.')
    else:
        form = PhoneNumberForm()
    return render(request, 'blood/verify_phone.html', {'form': form})

def verify_otp(request):
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            user = request.user
            
            if user.otp == otp and is_otp_valid(user.otp_created_at):
                user.is_phone_verified = True
                user.otp = None
                user.otp_created_at = None
                user.save()
                messages.success(request, 'Phone number verified successfully!')
                return redirect('afterlogin')
            else:
                messages.error(request, 'Invalid or expired OTP')
    else:
        form = OTPVerificationForm()
    return render(request, 'blood/verify_otp.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            if hasattr(phone_number, 'as_e164') and phone_number.as_e164:
                phone_number = phone_number.as_e164
            else:
                phone_number = str(phone_number).replace(' ', '')
            phone_number = to_python(phone_number)
            try:
                user = CustomUser.objects.get(phone_number=phone_number)
                otp = generate_otp()
                if send_otp_via_sms(phone_number, otp):
                    user.otp = otp
                    user.otp_created_at = datetime.now()
                    user.save()
                    request.session['reset_phone'] = str(phone_number)
                    return redirect('reset_password_otp')
                else:
                    messages.error(request, 'Failed to send OTP. Please try again.')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No user found with this phone number.')
    else:
        form = PhoneNumberForm()
    return render(request, 'blood/forgot_password.html', {'form': form})

def reset_password_otp(request):
    if 'reset_phone' not in request.session:
        return redirect('forgot_password')
        
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            phone_number = request.session['reset_phone']
            try:
                user = CustomUser.objects.get(phone_number=phone_number)
                if user.otp == otp and is_otp_valid(user.otp_created_at):
                    user.otp = None
                    user.otp_created_at = None
                    user.save()
                    return redirect('reset_password')
                else:
                    messages.error(request, 'Invalid or expired OTP')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found')
    else:
        form = OTPVerificationForm()
    return render(request, 'blood/reset_password_otp.html', {'form': form})

def reset_password(request):
    if 'reset_phone' not in request.session:
        return redirect('forgot_password')
        
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            phone_number = request.session['reset_phone']
            try:
                user = CustomUser.objects.get(phone_number=phone_number)
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                del request.session['reset_phone']
                messages.success(request, 'Password reset successful! Please login with your new password.')
                return redirect('patientlogin')
            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found')
    else:
        form = PasswordResetForm()
    return render(request, 'blood/reset_password.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            user = request.user
            if user.check_password(form.cleaned_data['current_password']):
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('afterlogin')
            else:
                messages.error(request, 'Current password is incorrect')
    else:
        form = ChangePasswordForm()
    return render(request, 'blood/change_password.html', {'form': form})