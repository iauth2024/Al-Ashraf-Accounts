from itertools import chain, count
import json
from pyexpat.errors import messages
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import datetime, timedelta, date, timezone
import logging

from .models import HeadOfAccount, Receipt, Voucher
from .forms import ReceiptForm, UploadExcelForm, VoucherFilterForm, VoucherForm, ApprovalForm, RejectionForm, DateRangeForm
from .utils import daterange, generate_auto_receipt_number

###################################################################################################################


from datetime import date, timedelta
from django.shortcuts import render
from django.db.models import Sum
from .models import Receipt, Voucher, UserActivityLog
from .forms import DateRangeForm

def dashboard(request):
    today = date.today()  # Use 'date' from 'datetime'

    form = DateRangeForm(request.GET or None)
    start_date = end_date = None

    if form.is_valid():
        date_range = form.cleaned_data['date_range']

        if date_range == 'today':
            start_date = end_date = today
        elif date_range == 'yesterday':
            start_date = end_date = today - timedelta(days=1)
        # Add more conditions for other date ranges as needed

    # Ensure default date range covers at least one day
    if not start_date or not end_date or start_date > end_date:
        start_date = end_date = today

    # Retrieve user's activities
    user_logs = UserActivityLog.objects.filter(timestamp__range=[start_date, end_date])
    
    # Calculate screen time, work time, logins, receipts created, and vouchers created
    screen_time = user_logs.aggregate(total=Sum('screen_time'))['total'] or 0
    work_time = user_logs.aggregate(total=Sum('work_time'))['total'] or 0
    logins = user_logs.count()
    total_receipts = Receipt.objects.filter(receipt_date__range=[start_date, end_date]).count()
    total_vouchers = Voucher.objects.filter(voucher_date__range=[start_date, end_date]).count()

    context = {
        'form': form,
        'screen_time': screen_time,
        'work_time': work_time,
        'logins': logins,
        'total_receipts': total_receipts,
        'total_vouchers': total_vouchers,
    }

    return render(request, 'dashboard.html', context)


###################################################################################################################
@login_required
def homepage(request):
    today = datetime.date.today()
    form = DateRangeForm(request.GET or None)
    
    start_date = end_date = None
    
    if form.is_valid():
        date_range = form.cleaned_data['date_range']
        
        if date_range == 'today':
            start_date = end_date = today
        elif date_range == 'yesterday':
            start_date = end_date = today - datetime.timedelta(days=1)
        elif date_range == 'this_week':
            start_date = today - datetime.timedelta(days=today.weekday())
            end_date = today
        elif date_range == 'last_week':
            start_date = today - datetime.timedelta(days=today.weekday() + 7)
            end_date = start_date + datetime.timedelta(days=6)
        elif date_range == 'this_month':
            start_date = today.replace(day=1)
            end_date = today
        elif date_range == 'last_month':
            first_day_of_this_month = today.replace(day=1)
            last_day_of_last_month = first_day_of_this_month - datetime.timedelta(days=1)
            start_date = last_day_of_last_month.replace(day=1)
            end_date = last_day_of_last_month
        elif date_range == 'custom':
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
    
    if not start_date or not end_date:
        start_date = today.replace(day=1)
        end_date = today

    # Datewise summaries for receipts and vouchers
    receipts_by_date = (
        Receipt.objects.filter(receipt_date__range=[start_date, end_date])
        .values('receipt_date')
        .annotate(total=Count('id'))
        .order_by('-receipt_date')
    )

    vouchers_by_date = (
        Voucher.objects.filter(voucher_date__range=[start_date, end_date])
        .values('voucher_date')
        .annotate(total=Count('id'))
        .order_by('-voucher_date')
    )

    voucher_status_by_date = (
        Voucher.objects.filter(voucher_date__range=[start_date, end_date])
        .values('voucher_date', 'status')
        .annotate(total=Count('id'))
        .order_by('-voucher_date', 'status')
    )

    # Initialize combined data dictionary
    combined_data = {}
    for item in receipts_by_date:
        date = item['receipt_date']
        combined_data[date] = {'receipts': item['total'], 'vouchers': 0, 'statuses': {'approved': 0, 'waiting': 0, 'rejected': 0}}

    for item in vouchers_by_date:
        date = item['voucher_date']
        if date not in combined_data:
            combined_data[date] = {'receipts': 0, 'vouchers': item['total'], 'statuses': {'approved': 0, 'waiting': 0, 'rejected': 0}}
        else:
            combined_data[date]['vouchers'] = item['total']

    for item in voucher_status_by_date:
        date = item['voucher_date']
        status = item['status']
        total = item['total']
        if date not in combined_data:
            combined_data[date] = {'receipts': 0, 'vouchers': 0, 'statuses': {'approved': 0, 'waiting': 0, 'rejected': 0}}
        combined_data[date]['statuses'][status] = total

    context = {
        'total_receipts': Receipt.objects.count(),
        'total_vouchers': Voucher.objects.count(),
        'combined_data': combined_data,
        'form': form,
    }

    return render(request, 'homepage.html', context)

from datetime import datetime


###################################################################################################################
from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)
def placeholder_view(request):
    return HttpResponse("This is a placeholder view")
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("Test view works!")

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('homepage')  # Redirect to homepage after login
        else:
            # Handle invalid login
            return render(request, 'login.html', {'error_message': 'Invalid username or password'})
    else:
        return render(request, 'login.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')  # Redirect to login page after logout
    else:
        # Handle GET requests by redirecting to the login page
        return redirect('login')

###################################################################################################################




# accounts/views.py


import logging

logger = logging.getLogger(__name__)


def create_receipt(request):
    if request.method == 'POST':
        form = ReceiptForm(request.POST)
        if form.is_valid():
            receipt = form.save(commit=False)
            if receipt.mode_of_payment in ['UPI', 'Bank Transfer', 'Cheque']:
                receipt.manual_receipt_no = Receipt.get_next_receipt_number(receipt.mode_of_payment)
            else:
                receipt.manual_receipt_no = form.cleaned_data.get('manual_receipt_no')
            receipt.save()
            messages.success(request, 'Receipt created successfully!')
            return redirect('receipt_success', receipt_id=receipt.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ReceiptForm(initial={'mode_of_payment': 'Cash'})
    
    return render(request, 'create_receipt.html', {'form': form})

def generate_auto_receipt_no(mode_of_payment):
    """
    Generate an auto-receipt number based on the mode of payment.
    """
    # Define prefix based on mode of payment
    if mode_of_payment == 'UPI':
        prefix = 'UPI-'
    elif mode_of_payment == 'Bank Transfer':
        prefix = 'BT-'
    elif mode_of_payment == 'Cheque':
        prefix = 'Cq-'
    else:
        prefix = ''

    # Get the last receipt for the given mode of payment
    last_receipt = Receipt.objects.filter(mode_of_payment=mode_of_payment).order_by('-id').first()

    # Determine the new receipt number
    if last_receipt and last_receipt.manual_receipt_no:
        try:
            # Extract and increment the number part
            last_number = int(last_receipt.manual_receipt_no.split('-')[-1])
            new_number = last_number + 1
        except ValueError:
            # Handle case where the receipt number cannot be converted to an integer
            new_number = 1
    else:
        # Start from 1 if there are no previous receipts
        new_number = 1

    # Return the formatted new receipt number
    return f"{prefix}{new_number:04d}"







def generate_receipt_number(mode_of_payment):
    prefix = {
        'UPI': 'UPI-',
        'Bank Transfer': 'BT-',
        'Cheque': 'CQ-'
    }.get(mode_of_payment, '')

    last_receipt = Receipt.objects.filter(mode_of_payment=mode_of_payment).order_by('-manual_receipt_no').first()
    if last_receipt and last_receipt.manual_receipt_no:
        try:
            last_number = int(last_receipt.manual_receipt_no.split('-')[-1])
            next_number = last_number + 1
        except ValueError:
            next_number = 1
    else:
        next_number = 1

    return f'{prefix}{next_number:04d}'





def receipt_success(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    return render(request, 'receipt_success.html', {'receipt': receipt})
###################################################################################################################
import datetime
from django.shortcuts import render
from django.http import HttpResponse
from .models import Receipt
import openpyxl
from io import BytesIO
from reportlab.lib.pagesizes import A4 # type: ignore
from reportlab.lib import colors # type: ignore
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph # type: ignore
from reportlab.lib.units import inch # type: ignore
from django.contrib.auth.decorators import login_required

@login_required
def list_receipts(request):
    receipts = Receipt.objects.all()

    # Apply search filters
    manual_book_no = request.GET.get('manual_book_no')
    if manual_book_no:
        receipts = receipts.filter(manual_book_no__icontains=manual_book_no)

    manual_receipt_no = request.GET.get('manual_receipt_no')
    if manual_receipt_no:
        receipts = receipts.filter(manual_receipt_no__icontains=manual_receipt_no)

    name = request.GET.get('name')
    if name:
        receipts = receipts.filter(name__icontains=name)

    phone = request.GET.get('phone')
    if phone:
        receipts = receipts.filter(phone__icontains=phone)

    type_of_receipt = request.GET.get('type_of_receipt')
    if type_of_receipt:
        receipts = receipts.filter(type_of_receipt__icontains=type_of_receipt)

    mode_of_payment = request.GET.get('mode_of_payment')
    if mode_of_payment:
        receipts = receipts.filter(mode_of_payment__icontains=mode_of_payment)

    transaction_id = request.GET.get('transaction_id')
    if transaction_id:
        receipts = receipts.filter(transaction_id__icontains=transaction_id)

    cheque_number = request.GET.get('cheque_number')
    if cheque_number:
        receipts = receipts.filter(cheque_number__icontains=cheque_number)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        receipts = receipts.filter(receipt_date__range=[start_date, end_date])

    # Pagination
    paginator = Paginator(receipts, 10)  # Show 10 receipts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'manual_book_no': manual_book_no,
        'manual_receipt_no': manual_receipt_no,
        'name': name,
        'phone': phone,
        'type_of_receipt': type_of_receipt,
        'mode_of_payment': mode_of_payment,
        'transaction_id': transaction_id,
        'cheque_number': cheque_number,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'list_receipts.html', context)

def download_receipts_excel(receipts):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=receipts.xlsx'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Receipts'

    headers = ['Manual Book No', 'Manual Receipt No', 'Name', 'Phone', 'Type of Receipt', 'Mode of Payment', 'Transaction ID', 'Cheque Number', 'Amount', 'Receipt Date']
    worksheet.append(headers)

    for receipt in receipts:
        row = [
            receipt.manual_book_no,
            receipt.manual_receipt_no,
            receipt.name,
            receipt.phone,
            receipt.type_of_receipt,
            receipt.mode_of_payment,
            receipt.transaction_id,
            receipt.cheque_number,
            receipt.amount,
            receipt.receipt_date.strftime('%Y-%m-%d')
        ]
        worksheet.append(row)

    workbook.save(response)
    return response

def download_receipts_pdf(receipts):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=receipts.pdf'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=10, leftMargin=10, topMargin=20, bottomMargin=20)

    elements = []
    data = [
        ['Manual B.No', 'Manual R.No', 'Name', 'Phone', 'Receipt type', 'Payment type', 'Txn ID', 'Cheque No', 'Amount', 'Receipt Date']
    ]

    # Set up a style for paragraphs
    styles = getSampleStyleSheet() # type: ignore
    styleN = styles['BodyText']
    styleN.wordWrap = 'CJK'  # Enable wrapping

    for receipt in receipts:
        row = [
            Paragraph(str(receipt.manual_book_no) if receipt.manual_book_no else '', styleN),
            Paragraph(str(receipt.manual_receipt_no) if receipt.manual_receipt_no else '', styleN),
            Paragraph(str(receipt.name) if receipt.name else '', styleN),
            Paragraph(str(receipt.phone) if receipt.phone else '', styleN),
            Paragraph(str(receipt.type_of_receipt) if receipt.type_of_receipt else '', styleN),
            Paragraph(str(receipt.mode_of_payment) if receipt.mode_of_payment else '', styleN),
            Paragraph(str(receipt.transaction_id) if receipt.transaction_id else '', styleN),
            Paragraph(str(receipt.cheque_number) if receipt.cheque_number else '', styleN),
            Paragraph(str(receipt.amount) if receipt.amount else '', styleN),
            Paragraph(receipt.receipt_date.strftime('%Y-%m-%d') if receipt.receipt_date else '', styleN)
        ]
        data.append(row)

    table = Table(data, colWidths=[0.75 * inch] * len(data[0]))
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


###################################################################################################################
@login_required
def convert_amount_to_words(request):
    amount = request.GET.get('amount')
    if amount:
        try:
            amount = float(amount)
            amount_in_words = num2words(amount) # type: ignore
            return JsonResponse({'amount_in_words': amount_in_words})
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
    return JsonResponse({'error': 'No amount provided'}, status=400)

@login_required
@staff_member_required
def approver_page(request):
    # Get search and filter parameters from GET request
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    entries_per_page = int(request.GET.get('entries_per_page', 10))

    # Build the query based on search and filter parameters
    vouchers = Voucher.objects.all()
    if search_query:
        vouchers = vouchers.filter(
            Q(voucher_no__icontains=search_query) |
            Q(paid_to__icontains=search_query) |
            Q(payment_purpose__icontains=search_query)
        )
    if status_filter:
        vouchers = vouchers.filter(status=status_filter)

    # Sort vouchers based on status
    sorted_vouchers = sorted(vouchers, key=lambda v: (
        v.status == 'approved',
        v.status == 'rejected',
        v.status not in ['waiting', 'waiting for approval']
    ))

    # Paginate sorted vouchers
    paginator = Paginator(sorted_vouchers, entries_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'approver_page.html', {
        'page_obj': page_obj,
        'entries_per_page': entries_per_page,
        'search_query': search_query,
        'status_filter': status_filter
    })

@login_required
def create_voucher(request):
    if request.method == 'POST':
        form = VoucherForm(request.POST)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.created_by = request.user
            voucher.save()
            messages.success(request, 'Voucher created successfully!')
            return redirect('voucher_success', voucher_id=voucher.id)
        else:
            # Collect form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = VoucherForm()
    
    return render(request, 'create_voucher.html', {'form': form})

@login_required
def voucher_success(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    return render(request, 'voucher_success.html', {'voucher': voucher})



@login_required
def edit_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    
    if request.method == 'POST':
        form = VoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            updated_voucher = form.save(commit=False)
            if any(field in form.changed_data for field in form.fields if field != 'status'):
                updated_voucher.status = 'waiting for approval'
            updated_voucher.save()
            return redirect('view_voucher', voucher_id=voucher.id)
    else:
        form = VoucherForm(instance=voucher)
    
    return render(request, 'edit_voucher.html', {'form': form, 'voucher': voucher})



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse

@login_required
@user_passes_test(lambda u: u.is_staff)
def view_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            voucher.status = 'approved'
            voucher.approved_by = request.user
            voucher.save()
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            if rejection_reason.strip() == '':
                return HttpResponseForbidden("Rejection reason is required.")
            voucher.status = 'rejected'
            voucher.rejection_reason = rejection_reason
            voucher.save()
        return redirect('view_voucher', voucher_id=voucher.id)

    return render(request, 'view_voucher.html', {'voucher': voucher})

@login_required
def edit_vouchers_list(request):
    vouchers = Voucher.objects.all()
    return render(request, 'edit_vouchers_list.html', {'vouchers': vouchers})



@login_required
@staff_member_required
def approve_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)

    if request.method == 'POST':
        form = ApprovalForm(request.POST, instance=voucher, user=request.user)
        if form.is_valid():
            voucher = form.save(commit=False)
            if 'reject' in request.POST:
                voucher.status = 'rejected'
            else:
                voucher.status = 'approved'
                voucher.approved_by = request.user
            voucher.save()
            return redirect('view_voucher', voucher_id=voucher.id)
    else:
        form = ApprovalForm(instance=voucher, user=request.user)

    return render(request, 'approve_voucher.html', {'form': form, 'voucher': voucher})



@login_required
@staff_member_required
def reject_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    
    if request.method == 'POST':
        form = RejectionForm(request.POST, instance=voucher)
        if form.is_valid():
            voucher = form.save(commit=False)
            voucher.status = 'rejected'
            voucher.save()
            return redirect('view_voucher', voucher_id=voucher_id)
    else:
        form = RejectionForm(instance=voucher)
    
    return render(request, 'reject_voucher.html', {'form': form, 'voucher': voucher})
from django.core.paginator import Paginator
###############################################################################################################################
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Voucher
import csv
import xlwt
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.pdfgen import canvas # type: ignore

@login_required
def list_vouchers(request):
    form = VoucherFilterForm(request.GET or None)
    vouchers = Voucher.objects.all()

    if form.is_valid():
        if form.cleaned_data['voucher_no']:
            vouchers = vouchers.filter(voucher_no__icontains=form.cleaned_data['voucher_no'])
        if form.cleaned_data['paid_to']:
            vouchers = vouchers.filter(paid_to__icontains=form.cleaned_data['paid_to'])
        if form.cleaned_data['on_account_of']:
            vouchers = vouchers.filter(on_account_of__icontains=form.cleaned_data['on_account_of'])
        if form.cleaned_data['head_of_account']:
            vouchers = vouchers.filter(head_of_account__name__icontains=form.cleaned_data['head_of_account'])
        if form.cleaned_data['mode_of_payment']:
            vouchers = vouchers.filter(mode_of_payment=form.cleaned_data['mode_of_payment'])
        if form.cleaned_data['transaction_id']:
            vouchers = vouchers.filter(transaction_id__icontains=form.cleaned_data['transaction_id'])
        if form.cleaned_data['amount_min'] is not None:
            vouchers = vouchers.filter(amount__gte=form.cleaned_data['amount_min'])
        if form.cleaned_data['amount_max'] is not None:
            vouchers = vouchers.filter(amount__lte=form.cleaned_data['amount_max'])
        if form.cleaned_data['start_date']:
            vouchers = vouchers.filter(voucher_date__gte=form.cleaned_data['start_date'])
        if form.cleaned_data['end_date']:
            vouchers = vouchers.filter(voucher_date__lte=form.cleaned_data['end_date'])
        if form.cleaned_data['received_by']:
            vouchers = vouchers.filter(received_by__icontains=form.cleaned_data['received_by'])
        if form.cleaned_data['status']:
            vouchers = vouchers.filter(status=form.cleaned_data['status'])

    paginator = Paginator(vouchers, 10)  # Show 10 vouchers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'list_vouchers.html', {
        'form': form,
        'page_obj': page_obj
    })

def download_vouchers(vouchers, download_format):
    if download_format == 'excel':
        return download_excel(vouchers)
    elif download_format == 'pdf':
        return download_pdf(vouchers)
    else:
        return HttpResponse(status=400)
from django.http import HttpResponse
from openpyxl import Workbook
from io import BytesIO
from .models import Voucher




def download_excel(request):
    # Queryset for all vouchers
    vouchers = Voucher.objects.all()

    # Create a new Excel workbook and add a worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = 'Vouchers'

    # Define the columns, including 'Approved By'
    columns = [
        'Voucher No', 'Paid To', 'On Account Of', 'Head Of Account',
        'Mode Of Payment', 'Transaction ID', 'Amount', 'Date', 'Received By', 'Status', 'Approved By'
    ]

    # Write the column headers to the worksheet
    for col_num, column_title in enumerate(columns, 1):
        ws.cell(row=1, column=col_num, value=column_title)

    # Write the rows to the worksheet
    rows = vouchers.values_list(
        'voucher_no', 'paid_to', 'on_account_of', 'head_of_account__name',
        'mode_of_payment', 'transaction_id', 'amount', 'voucher_date',
        'received_by', 'status', 'approved_by__username'  # Change to username or use other attribute
    )
    for row_num, row in enumerate(rows, 2):
        for col_num, cell_value in enumerate(row, 1):
            ws.cell(row=row_num, column=col_num, value=cell_value)

    # Save the workbook to a BytesIO buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Set the HTTP response content type to Excel format
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="vouchers.xlsx"'
    return response


from reportlab.lib.pagesizes import A4, landscape # type: ignore



def download_pdf(request):
    # Queryset for all vouchers
    vouchers = Voucher.objects.all()

    # Create a PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))  # Set pagesize to landscape A4
    elements = []

    # Define the columns, including 'Approved By'
    columns = [
        'Voucher No', 'Paid To', 'On Account Of', 'Head Of Account',
        'Mode Of Payment', 'Transaction ID', 'Amount', 'Date', 'Received By', 'Status', 'Approved By'
    ]

    # Fetch the rows from the queryset
    rows = vouchers.values_list(
        'voucher_no', 'paid_to', 'on_account_of', 'head_of_account__name',
        'mode_of_payment', 'transaction_id', 'amount', 'voucher_date',
        'received_by', 'status', 'approved_by__username'  # Change to username or use other attribute
    )

    # Create a table data structure for PDF
    data = [columns] + [list(row) for row in rows]

    # Create the table and style it
    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Adjust font size to fit more content
        ('ALIGN', (0, 1), (-1, -1), 'LEFT')  # Align text to the left for readability
    ])
    table.setStyle(style)
    elements.append(table)

    # Build the PDF document
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="vouchers.pdf"'
    return response


#####################################################################################################################
def delete_voucher(request, voucher_id):
    voucher = get_object_or_404(Voucher, id=voucher_id)
    voucher.delete()
    # Redirect to a success page or another appropriate URL
    return redirect('list_vouchers')  # Assuming 'list_vouchers' is the name of your list view

###################################################################################################################

class CustomPasswordResetView(auth_views.PasswordResetView):
    template_name = 'custom_password_reset.html'
    email_template_name = 'custom_password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'custom_password_reset_done.html'

class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'custom_password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'custom_password_reset_complete.html'



####################################################################################################################



################################################################################



class DateRangeForm(forms.Form):
    DATE_RANGE_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('custom', 'Custom'),
    ]
    
    date_range = forms.ChoiceField(choices=DATE_RANGE_CHOICES)
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))

def get_date_range(date_range):
    today = timezone.now().date()
    if date_range == 'today':
        start_date = end_date = today
    elif date_range == 'yesterday':
        start_date = end_date = today - timedelta(days=1)
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif date_range == 'last_month':
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        start_date = last_day_of_last_month.replace(day=1)
        end_date = last_day_of_last_month
    else:
        start_date = end_date = today
    return start_date, end_date

def ledger_page(request):
    form = DateRangeForm(request.GET or None)

    # Get the current date
    today = timezone.now().date()

    # Set default start date as the start of the financial year (assuming April 1)
    financial_year_start = date(today.year if today.month >= 4 else today.year - 1, 4, 1)

    # Get date range from the form or set default
    if form.is_valid():
        date_range = form.cleaned_data['date_range']
        start_date, end_date = get_date_range(date_range)

        if date_range == 'custom':
            start_date = form.cleaned_data['start_date'] or financial_year_start
            end_date = form.cleaned_data['end_date'] or today
    else:
        start_date = financial_year_start
        end_date = today

    # Debugging output
    print(f"Start Date: {start_date}, End Date: {end_date}")

    # Fetch transactions within the date range
    receipts = Receipt.objects.filter(receipt_date__range=[start_date, end_date])
    vouchers = Voucher.objects.filter(voucher_date__range=[start_date, end_date])

    # Debugging output
    print(f"Receipts Count: {receipts.count()}, Vouchers Count: {vouchers.count()}")

    # Combine receipts and vouchers into a single list
    transactions = sorted(
        chain(receipts, vouchers),
        key=lambda x: x.receipt_date if hasattr(x, 'receipt_date') else x.voucher_date
    )

    # Paginate the transactions list
    paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'start_date': start_date,
        'end_date': end_date,
        'today': today,
    }
    return render(request, 'ledger.html', context)
 ###############################################################################################################


from django.db.models import Count, Sum
from django.shortcuts import render
from .models import Receipt, Voucher
from .forms import DateRangeForm
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, F
from django.utils import timezone

def get_date_range(date_range):
    today = timezone.now().date()
    if date_range == 'today':
        start_date = end_date = today
    elif date_range == 'yesterday':
        start_date = end_date = today - timedelta(days=1)
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif date_range == 'last_month':
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        start_date = last_day_of_last_month.replace(day=1)
        end_date = last_day_of_last_month
    else:
        start_date = end_date = today
    return start_date, end_date


@login_required
@staff_member_required
def ledger_page_details(request):
    # Instantiate the date form
    date_form = DateRangeForm(request.GET or None)

    # Initialize date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter data based on the date range if provided
    receipts_query = Receipt.objects.all()
    vouchers_query = Voucher.objects.all()

    if start_date and end_date:
        receipts_query = receipts_query.filter(receipt_date__range=[start_date, end_date])
        vouchers_query = vouchers_query.filter(voucher_date__range=[start_date, end_date])

    # Calculate total amounts for receipts and vouchers
    total_receipts_amount = receipts_query.aggregate(Sum('amount'))['amount__sum'] or 1  # Avoid division by zero
    total_vouchers_amount = vouchers_query.aggregate(Sum('amount'))['amount__sum'] or 1

    # Summarize receipts
    receipt_summary = receipts_query.values('type_of_receipt').annotate(
        count=Count('id'),
        total_amount=Sum('amount'),
        percentage=Sum('amount') * 100 / total_receipts_amount
    )

    # Summarize vouchers
    voucher_summary = vouchers_query.values('head_of_account__name').annotate(
        count=Count('id'),
        total_amount=Sum('amount'),
        percentage=Sum('amount') * 100 / total_vouchers_amount
    )

    context = {
        'date_form': date_form,
        'receipt_summary': receipt_summary,
        'voucher_summary': voucher_summary,
    }

    return render(request, 'ledger_page_details.html', context)



def receipt_detail(request, type_of_receipt):
    date_form = DateRangeForm(request.GET or None)
    date_range = date_form.cleaned_data if date_form.is_valid() else {}
    
    # Filter Receipts based on type and date range
    receipts = Receipt.objects.filter(type_of_receipt=type_of_receipt)
    if date_range:
        start_date, end_date = get_date_range(date_range.get('date_range', 'today'))
        receipts = receipts.filter(receipt_date__range=[start_date, end_date])
    
    context = {
        'receipts': receipts,
        'type_of_receipt': type_of_receipt,
        'date_form': date_form
    }
    return render(request, 'receipt_detail.html', context)


def voucher_detail(request, head_of_account):
    date_form = DateRangeForm(request.GET or None)
    date_range = date_form.cleaned_data if date_form.is_valid() else {}
    
    # Filter Vouchers based on head_of_account and date range
    vouchers = Voucher.objects.filter(head_of_account__name=head_of_account)
    if date_range:
        start_date, end_date = get_date_range(date_range.get('date_range', 'today'))
        vouchers = vouchers.filter(voucher_date__range=[start_date, end_date])
    
    context = {
        'vouchers': vouchers,
        'head_of_account': head_of_account,
        'date_form': date_form
    }
    return render(request, 'voucher_detail.html', context)






###############################################################################################################



def trail_balance(request):
    # Get the date range from the request, default to the current financial year
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    financial_year = request.GET.get('financial_year')
    
    # Default to financial year start if no dates provided
    if not start_date:
        if financial_year:
            start_date = f"{financial_year}-04-01"
        else:
            start_date = date.today().replace(day=1, month=4).strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')

    try:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)
    except ValueError:
        start_date = date.today().replace(day=1, month=4)
        end_date = date.today()

    # Get all Receipts and Vouchers within the date range
    receipts = Receipt.objects.filter(receipt_date__range=(start_date, end_date))
    vouchers = Voucher.objects.filter(voucher_date__range=(start_date, end_date))

    # Calculate totals for receipts and vouchers
    total_receipts = receipts.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    total_vouchers = vouchers.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    # Group Receipts and Vouchers by type of receipt and head of account
    receipt_groups = receipts.values('type_of_receipt').annotate(total_amount=Sum('amount'))
    voucher_groups = vouchers.values('head_of_account').annotate(total_amount=Sum('amount'))

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'financial_year': financial_year,
        'total_receipts': total_receipts,
        'total_vouchers': total_vouchers,
        'receipt_groups': receipt_groups,
        'voucher_groups': voucher_groups
    }

    return render(request, 'trail_balance.html', context)

################################################################################################################################


from django.shortcuts import render
from django.db.models import Sum
from datetime import date, timedelta
from .forms import DateRangeForm
from .models import Receipt, Voucher

def day_book(request):
    form = DateRangeForm(request.POST or None)
    opening_balance_cash = 0
    closing_balance_cash = 0
    opening_balance_bank = 0
    closing_balance_bank = 0
    total_receipts_cash = 0
    total_receipts_bank = 0
    total_payments_cash = 0
    total_payments_bank = 0
    include_contra = False  # Default to not include contra

    if form.is_valid():
        start_date, end_date = get_date_range(form.cleaned_data['date_range'])
        if form.cleaned_data['date_range'] == 'custom':
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
        include_contra = form.cleaned_data.get('include_contra', False)  # Default to False if not set

        # Cash Transactions
        opening_balance_cash = fetch_opening_balance_cash(start_date)
        total_receipts_cash = fetch_total_receipts_cash(start_date, end_date)
        total_payments_cash = fetch_total_payments_cash(start_date, end_date)
        closing_balance_cash = opening_balance_cash + total_receipts_cash - total_payments_cash

        # Bank Transactions
        opening_balance_bank = fetch_opening_balance_bank(start_date)
        total_receipts_bank = fetch_total_receipts_bank(start_date, end_date)
        total_payments_bank = fetch_total_payments_bank(start_date, end_date)
        closing_balance_bank = opening_balance_bank + total_receipts_bank - total_payments_bank

        # Include Contra Entries if checked
        if include_contra:
            contra_entries = Contra.objects.filter(date__range=[start_date, end_date])
            for contra in contra_entries:
                if contra.contra_type == 'withdraw':
                    closing_balance_bank -= contra.amount
                    closing_balance_cash += contra.amount
                elif contra.contra_type == 'deposit':
                    closing_balance_cash -= contra.amount
                    closing_balance_bank += contra.amount

    context = {
        'form': form,
        'opening_balance_cash': opening_balance_cash,
        'closing_balance_cash': closing_balance_cash,
        'opening_balance_bank': opening_balance_bank,
        'closing_balance_bank': closing_balance_bank,
        'total_receipts_cash': total_receipts_cash,
        'total_payments_cash': total_payments_cash,
        'total_receipts_bank': total_receipts_bank,
        'total_payments_bank': total_payments_bank,
        'include_contra': include_contra,
    }

    return render(request, 'day_book.html', context)


def get_date_range(date_range):
    today = date.today()
    if date_range == 'today':
        start_date = end_date = today
    elif date_range == 'yesterday':
        start_date = end_date = today - timedelta(days=1)
    elif date_range == 'this_week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif date_range == 'last_week':
        start_date = today - timedelta(days=today.weekday() + 7)
        end_date = start_date + timedelta(days=6)
    elif date_range == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif date_range == 'last_month':
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        start_date = last_day_of_last_month.replace(day=1)
        end_date = last_day_of_last_month
    else:
        start_date = end_date = today
    return start_date, end_date

def fetch_opening_balance_cash(date, include_contra=False):
    receipts = Receipt.objects.filter(receipt_date__lt=date, mode_of_payment='Cash').aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    vouchers = Voucher.objects.filter(voucher_date__lt=date, mode_of_payment='cash').aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    opening_balance = receipts - vouchers

    if include_contra:
        contra_entries = Contra.objects.filter(date__lt=date)
        for contra in contra_entries:
            if contra.contra_type == 'withdraw':
                opening_balance -= contra.amount
            elif contra.contra_type == 'deposit':
                opening_balance += contra.amount

    return opening_balance


def fetch_total_receipts_cash(start_date, end_date):
    return Receipt.objects.filter(receipt_date__range=[start_date, end_date], mode_of_payment='Cash').aggregate(total_amount=Sum('amount'))['total_amount'] or 0

def fetch_total_payments_cash(start_date, end_date):
    return Voucher.objects.filter(voucher_date__range=[start_date, end_date], mode_of_payment='cash').aggregate(total_amount=Sum('amount'))['total_amount'] or 0

def fetch_opening_balance_bank(date, include_contra=False):
    receipts = Receipt.objects.filter(receipt_date__lt=date, mode_of_payment__in=['UPI', 'Cheque', 'Bank Transfer']).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    vouchers = Voucher.objects.filter(voucher_date__lt=date, mode_of_payment__in=['bank_transfer', 'cheque']).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    opening_balance = receipts - vouchers

    if include_contra:
        contra_entries = Contra.objects.filter(date__lt=date)
        for contra in contra_entries:
            if contra.contra_type == 'withdraw':
                opening_balance += contra.amount
            elif contra.contra_type == 'deposit':
                opening_balance -= contra.amount

    return opening_balance


def fetch_total_receipts_bank(start_date, end_date):
    return Receipt.objects.filter(receipt_date__range=[start_date, end_date], mode_of_payment__in=['UPI', 'Cheque', 'Bank Transfer']).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

def fetch_total_payments_bank(start_date, end_date):
    return Voucher.objects.filter(voucher_date__range=[start_date, end_date], mode_of_payment__in=['bank_transfer', 'cheque']).aggregate(total_amount=Sum('amount'))['total_amount'] or 0


from django import forms

class DateRangeForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    date_range = forms.ChoiceField(
        choices=[
            ('today', 'Today'),
            ('yesterday', 'Yesterday'),
            ('this_week', 'This Week'),
            ('last_week', 'Last Week'),
            ('this_month', 'This Month'),
            ('last_month', 'Last Month'),
            ('custom', 'Custom'),
        ]
    )
    include_contra = forms.BooleanField(required=False, initial=False, label='Include Contra Transactions')


###############################################################################################################



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ContraForm
from .models import Contra, Balance
from django.utils import timezone

@login_required
def create_contra(request):
    if request.method == 'POST':
        form = ContraForm(request.POST)
        if form.is_valid():
            contra = form.save(commit=False)
            contra.performed_by = request.user
            contra.date = timezone.now()  # Set the current date and time
            
            # Fetch current balances
            balances = fetch_balances(contra.date, contra.date)
            
            if contra.contra_type == 'withdraw':
                if contra.amount <= balances['closing_balance_bank']:
                    balances['closing_balance_bank'] -= contra.amount
                    balances['closing_balance_cash'] += contra.amount
                else:
                    return render(request, 'create_contra.html', {'form': form, 'error': 'Insufficient bank balance.'})
            elif contra.contra_type == 'deposit':
                if contra.amount <= balances['closing_balance_cash']:
                    balances['closing_balance_cash'] -= contra.amount
                    balances['closing_balance_bank'] += contra.amount
                else:
                    return render(request, 'create_contra.html', {'form': form, 'error': 'Insufficient cash balance.'})
            else:
                return render(request, 'create_contra.html', {'form': form, 'error': 'Invalid contra type.'})

            # Update the balance records
            balance, created = Balance.objects.get_or_create()  # Ensure there's a Balance record
            balance.cash_balance = balances['closing_balance_cash']
            balance.non_cash_balance = balances['closing_balance_bank']
            balance.save()

            contra.save()
            return redirect('list_contra')

    else:
        form = ContraForm()
    return render(request, 'create_contra.html', {'form': form})

from .forms import ContraFilterForm

@login_required
def list_contra(request):
    # Initialize filter form
    form = ContraFilterForm(request.GET or None)
    contras = Contra.objects.all()

    if form.is_valid():
        contra_no = form.cleaned_data.get('contra_no')
        date = form.cleaned_data.get('date')
        amount_min = form.cleaned_data.get('amount_min')
        amount_max = form.cleaned_data.get('amount_max')
        contra_type = form.cleaned_data.get('contra_type')
        performed_by = form.cleaned_data.get('performed_by')

        if contra_no:
            contras = contras.filter(contra_no=contra_no)
        if date:
            contras = contras.filter(date=date)
        if amount_min:
            contras = contras.filter(amount__gte=amount_min)
        if amount_max:
            contras = contras.filter(amount__lte=amount_max)
        if contra_type:
            contras = contras.filter(contra_type=contra_type)
        if performed_by:
            contras = contras.filter(performed_by__username=performed_by)

    context = {
        'form': form,
        'contras': contras
    }

    return render(request, 'list_contra.html', context)


@login_required
def delete_contra(request, contra_no):
    contra = get_object_or_404(Contra, pk=contra_no)
    if request.method == 'POST':
        # Handle the balance adjustments if necessary
        balances = fetch_balances(contra.date, contra.date)
        
        if contra.contra_type == 'withdraw':
            balances['closing_balance_bank'] += contra.amount
            balances['closing_balance_cash'] -= contra.amount
        elif contra.contra_type == 'deposit':
            balances['closing_balance_cash'] += contra.amount
            balances['closing_balance_bank'] -= contra.amount
        
        # Update the balance records
        balance, created = Balance.objects.get_or_create()
        balance.cash_balance = balances['closing_balance_cash']
        balance.non_cash_balance = balances['closing_balance_bank']
        balance.save()
        
        contra.delete()
        return redirect('list_contra')
    
    return render(request, 'delete_contra.html', {'contra': contra})
def fetch_balances(start_date, end_date):
    balance = Balance.objects.first()  # Get the most recent balance record
    if balance:
        return {
            'closing_balance_cash': balance.cash_balance,
            'closing_balance_bank': balance.non_cash_balance
        }
    else:
        return {
            'closing_balance_cash': 0,
            'closing_balance_bank': 0
        }

import pandas as pd
from django.http import HttpResponse
from .models import Contra

def download_contra_excel(request):
    # Fetch contra transactions
    contras = Contra.objects.all()
    
    # Create a DataFrame
    df = pd.DataFrame(list(contras.values('contra_no', 'date', 'amount', 'contra_type', 'performed_by')))
    
    # Create an HttpResponse object with Excel content type
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=contra_transactions.xlsx'
    
    # Write DataFrame to the response
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Contras')
    
    return response



def download_contra_pdf(request):
    # Fetch contra transactions from the database
    contras = Contra.objects.all()  # Add any necessary filtering here

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=contra_transactions.pdf'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=10, leftMargin=10, topMargin=20, bottomMargin=20)

    elements = []
    data = [
        ['Contra No', 'Date', 'Amount', 'Type', 'Performed By']
    ]

    # Set up a style for paragraphs
    styles = getSampleStyleSheet() # type: ignore
    styleN = styles['BodyText']
    styleN.wordWrap = 'CJK'  # Enable wrapping

    for contra in contras:
        row = [
            Paragraph(str(contra.contra_no) if contra.contra_no else '', styleN),
            Paragraph(contra.date.strftime('%Y-%m-%d') if contra.date else '', styleN),
            Paragraph(str(contra.amount) if contra.amount else '', styleN),
            Paragraph(contra.get_contra_type_display() if contra.contra_type else '', styleN),
            Paragraph(str(contra.performed_by) if contra.performed_by else '', styleN),
        ]
        data.append(row)

    table = Table(data, colWidths=[1.0 * inch] * len(data[0]))
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

###############################################################################################################################


from django.shortcuts import render, redirect
from django.contrib import messages
import pandas as pd
from .forms import UploadExcelForm
from .models import Receipt

def upload_receipt_from_excel(request):
    if request.method == 'POST':
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)
            
            success_count = 0
            fail_count = 0
            failed_rows = []
            failed_reasons = []
            total_rows = len(df)

            for index, row in df.iterrows():
                try:
                    receipt_date = pd.to_datetime(row.get('Receipt Date'), errors='coerce')
                    mode_of_payment = row.get('Mode of Payment')
                    type_of_receipt = row.get('Type of Receipt')
                    amount = row.get('Amount')

                    missing_fields = []
                    if pd.isnull(type_of_receipt):
                        missing_fields.append('Type of Receipt')
                    if pd.isnull(amount):
                        missing_fields.append('Amount')
                    if pd.isnull(receipt_date):
                        missing_fields.append('Receipt Date')

                    if mode_of_payment == 'Cash':
                        if pd.isnull(row.get('Manual Book No')):
                            missing_fields.append('Manual Book No')
                        if pd.isnull(row.get('Manual Receipt No')):
                            missing_fields.append('Manual Receipt No')

                    if mode_of_payment == 'Cheque' and pd.isnull(row.get('Cheque Number')):
                        missing_fields.append('Cheque Number')
                    
                    if mode_of_payment != 'Cash' and pd.isnull(row.get('Manual Receipt No')):
                        manual_receipt_no = Receipt.get_next_receipt_number(mode_of_payment)
                    else:
                        manual_receipt_no = row.get('Manual Receipt No')

                    if missing_fields:
                        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                    transaction_id = row.get('Transaction ID') if not pd.isnull(row.get('Transaction ID')) else None
                    cheque_number = row.get('Cheque Number') if not pd.isnull(row.get('Cheque Number')) else None

                    receipt = Receipt(
                        manual_book_no=row.get('Manual Book No') if mode_of_payment == 'Cash' else None,
                        manual_receipt_no=manual_receipt_no,
                        name=row.get('Name'),
                        phone=row.get('Phone'),
                        address=row.get('Address', ''),
                        type_of_receipt=type_of_receipt,
                        mode_of_payment=mode_of_payment,
                        transaction_id=transaction_id,
                        cheque_number=cheque_number,
                        amount=amount,
                        receipt_date=receipt_date
                    )
                    receipt.save()
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_rows.append(index)
                    failed_reasons.append(f"Row {index + 1}: {str(e)}")
                
                # Update progress bar (assuming an AJAX call to update progress on the client side)
                progress = (index + 1) / total_rows * 100
                request.session['upload_progress'] = progress

            # Prepare upload report
            report = f"Upload Summary:\n\n"
            report += f"Total Rows Processed: {total_rows}\n"
            report += f"Successful Uploads: {success_count}\n"
            report += f"Failed Uploads: {fail_count}\n\n"
            report += "Failure Details:\n"
            for reason in failed_reasons:
                report += reason + '\n'

            # Store report in session
            request.session['upload_report'] = report

            # Display success and error messages
            messages.success(request, f'Successfully uploaded {success_count} receipts.')
            if fail_count > 0:
                messages.error(request, f'Failed to upload {fail_count} receipts.')

            return redirect('upload_receipt_success')
    else:
        form = UploadExcelForm()
    return render(request, 'upload_receipt_from_excel.html', {'form': form})

def upload_progress(request):
    return render(request, 'upload_progress.html')

def upload_receipt_success(request):
    return render(request, 'upload_receipt_success.html')

###############################################################################################################################




import pandas as pd
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Voucher, HeadOfAccount
from .forms import ExcelUploadForm



def upload_vouchers_from_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)

            success_count = 0
            fail_count = 0
            failed_rows = []
            failed_reasons = []
            total_rows = len(df)
            already_exists = 0

            # Get the current user to set as `created_by`
            current_user = request.user

            for index, row in df.iterrows():
                try:
                    # Extract and clean data
                    voucher_date = pd.to_datetime(row.get('Date'), errors='coerce')
                    mode_of_payment = row.get('Mode Of Payment')
                    transaction_id = row.get('Transaction ID') if not pd.isnull(row.get('Transaction ID')) else None
                    amount = row.get('Amount')
                    
                    # Initialize an empty list to collect missing fields
                    missing_fields = []

                    # Check for missing required fields
                    if pd.isnull(row.get('Voucher No')):
                        missing_fields.append('Voucher No')
                    if pd.isnull(row.get('Paid To')):
                        missing_fields.append('Paid To')
                    if pd.isnull(row.get('On Account Of')):
                        missing_fields.append('On Account Of')
                    if pd.isnull(row.get('Head Of Account')):
                        missing_fields.append('Head Of Account')
                    if pd.isnull(mode_of_payment):
                        missing_fields.append('Mode Of Payment')
                    if pd.isnull(amount):
                        missing_fields.append('Amount')
                    if pd.isnull(voucher_date):
                        missing_fields.append('Date')

                    # Check for 'Approved By' only if status is 'approved'
                    approved_by = row.get('Approved By')
                    status = row.get('Status').strip().lower()  # Normalize status field
                    if status == 'approved':
                        if pd.isnull(approved_by):
                            missing_fields.append('Approved By')
                        else:
                            try:
                                approved_by_user = User.objects.get(username=approved_by.strip())
                            except User.DoesNotExist:
                                raise ValueError(f"User '{approved_by}' does not exist")
                    else:
                        approved_by_user = None

                    if mode_of_payment == 'bank_transfer' or mode_of_payment == 'cheque':
                        if pd.isnull(transaction_id):
                            missing_fields.append('Transaction ID')

                    if missing_fields:
                        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                    # Fetch or create HeadOfAccount instance
                    head_of_account_name = row.get('Head Of Account')
                    head_of_account, created = HeadOfAccount.objects.get_or_create(name=head_of_account_name)

                    # Check for existing vouchers with the same number
                    if Voucher.objects.filter(voucher_no=row.get('Voucher No')).exists():
                        already_exists += 1
                        continue  # Skip to the next row

                    # Create Voucher instance
                    voucher = Voucher(
                        voucher_no=row.get('Voucher No'),
                        paid_to=row.get('Paid To'),
                        on_account_of=row.get('On Account Of'),
                        head_of_account=head_of_account,
                        mode_of_payment=mode_of_payment,
                        transaction_id=transaction_id,
                        amount=amount,
                        voucher_date=voucher_date,
                        received_by=row.get('Received By'),
                        approved_by=approved_by_user,
                        created_by=current_user  # Set created_by to the current user
                    )
                    voucher.save()
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_rows.append(index)
                    failed_reasons.append(f"Row {index + 1}: {str(e)}")

                # Update progress bar (assuming an AJAX call to update progress on the client side)
                progress = (index + 1) / total_rows * 100
                request.session['upload_progress'] = progress

            # Prepare upload report
            report = f"Upload Summary:\n\n"
            report += f"Total Rows Processed: {total_rows}\n"
            report += f"Successful Uploads: {success_count}\n"
            report += f"Failed Uploads: {fail_count}\n"
            report += f"Already Exists: {already_exists}\n\n"
            report += "Failure Details:\n"
            for reason in failed_reasons:
                report += reason + '\n'

            # Store report in session
            request.session['upload_report'] = report

            # Display success and error messages
            messages.success(request, f'Successfully uploaded {success_count} vouchers.')
            if fail_count > 0:
                messages.error(request, f'Failed to upload {fail_count} vouchers.')

            return redirect('upload_vouchers_success')
    else:
        form = ExcelUploadForm()
    return render(request, 'upload_vouchers_from_excel.html', {'form': form})




import pandas as pd
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Voucher, HeadOfAccount
from .forms import ExcelUploadForm

def upload_vouchers_from_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            df = pd.read_excel(excel_file)

            success_count = 0
            fail_count = 0
            failed_rows = []
            failed_reasons = []
            total_rows = len(df)
            already_exists = 0

            # Get the current user to set as `created_by`
            current_user = request.user

            for index, row in df.iterrows():
                try:
                    # Extract and clean data
                    voucher_date = pd.to_datetime(row.get('Date'), errors='coerce')
                    mode_of_payment = row.get('Mode Of Payment')
                    transaction_id = row.get('Transaction ID') if not pd.isnull(row.get('Transaction ID')) else None
                    amount = row.get('Amount')
                    
                    # Initialize an empty list to collect missing fields
                    missing_fields = []

                    # Check for missing required fields
                    if pd.isnull(row.get('Voucher No')):
                        missing_fields.append('Voucher No')
                    if pd.isnull(row.get('Paid To')):
                        missing_fields.append('Paid To')
                    if pd.isnull(row.get('On Account Of')):
                        missing_fields.append('On Account Of')
                    if pd.isnull(row.get('Head Of Account')):
                        missing_fields.append('Head Of Account')
                    if pd.isnull(mode_of_payment):
                        missing_fields.append('Mode Of Payment')
                    if pd.isnull(amount):
                        missing_fields.append('Amount')
                    if pd.isnull(voucher_date):
                        missing_fields.append('Date')

                    # Check for 'Approved By' only if status is 'approved'
                    approved_by = row.get('Approved By')
                    status = row.get('Status').strip().lower()  # Normalize status field

                    if status == 'approved':
                        if pd.isnull(approved_by):
                            missing_fields.append('Approved By')
                        else:
                            try:
                                approved_by_user = User.objects.get(username=approved_by.strip())
                            except User.DoesNotExist:
                                raise ValueError(f"User '{approved_by}' does not exist")
                    else:
                        approved_by_user = None

                    if mode_of_payment == 'bank_transfer' or mode_of_payment == 'cheque':
                        if pd.isnull(transaction_id):
                            missing_fields.append('Transaction ID')

                    if missing_fields:
                        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                    # Fetch or create HeadOfAccount instance
                    head_of_account_name = row.get('Head Of Account')
                    head_of_account, created = HeadOfAccount.objects.get_or_create(name=head_of_account_name)

                    # Check for existing vouchers with the same number
                    if Voucher.objects.filter(voucher_no=row.get('Voucher No')).exists():
                        already_exists += 1
                        continue  # Skip to the next row

                    # Create Voucher instance
                    voucher = Voucher(
                        voucher_no=row.get('Voucher No'),
                        paid_to=row.get('Paid To'),
                        on_account_of=row.get('On Account Of'),
                        head_of_account=head_of_account,
                        mode_of_payment=mode_of_payment,
                        transaction_id=transaction_id,
                        amount=amount,
                        voucher_date=voucher_date,
                        received_by=row.get('Received By'),
                        approved_by=approved_by_user,
                        created_by=current_user  # Set created_by to the current user
                    )
                    # Set the status explicitly
                    voucher.status = status  # Update status field
                    voucher.save()
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_rows.append(index)
                    failed_reasons.append(f"Row {index + 1}: {str(e)}")

                # Update progress bar (assuming an AJAX call to update progress on the client side)
                progress = (index + 1) / total_rows * 100
                request.session['upload_progress'] = progress

            # Prepare upload report
            report = f"Upload Summary:\n\n"
            report += f"Total Rows Processed: {total_rows}\n"
            report += f"Successful Uploads: {success_count}\n"
            report += f"Failed Uploads: {fail_count}\n"
            report += f"Already Exists: {already_exists}\n\n"
            report += "Failure Details:\n"
            for reason in failed_reasons:
                report += reason + '\n'

            # Store report in session
            request.session['upload_report'] = report

            # Display success and error messages
            messages.success(request, f'Successfully uploaded {success_count} vouchers.')
            if fail_count > 0:
                messages.error(request, f'Failed to upload {fail_count} vouchers.')

            return redirect('upload_vouchers_success')
    else:
        form = ExcelUploadForm()
    return render(request, 'upload_vouchers_from_excel.html', {'form': form})

def upload_vouchers_success(request):
    return render(request, 'upload_vouchers_success.html')