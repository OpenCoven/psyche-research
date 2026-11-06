import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, OperationalError
from django.db.models import Max, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from . import services
from .forms import MAX_ARTIFACT_LINKS, SubmissionForm, DecisionForm, CapacityForm, ReasonForm, WithdrawalForm
from .models import Capacity, Submission, Version, Work, Report, Appeal, Decision

# All private form payloads are sensitive to Django exception reporting.
def fail(request,exc,template=None,context=None):
    if exc.status == 404:
        raise Http404
    if template:
        context=context or {}
        context['error']=str(exc)
        return render(request,template,context,status=exc.status)
    return HttpResponse(str(exc),status=exc.status,content_type='text/plain')

def moderator_required(view):
    from functools import wraps
    @wraps(view)
    @login_required
    def wrapped(request,*args,**kwargs):
        if not services.is_moderator(request.user):
            return HttpResponse('Human moderator access is required.',status=403)
        return view(request,*args,**kwargs)
    return wrapped

# Public field limits are read from the model so the published description cannot drift from validation.
PUBLIC_FIELD_LIMITS = (('title','Title'),('byline','Public author names'),('abstract','Abstract'),('methods','Methods or linked methods'),
    ('claims','Results and claims'),('limitations','Limitations'),('artifacts','Artifact links, all together'),('provenance','Provenance'),('ai_disclosure','AI assistance disclosure'),
    ('change_note','Revision or correction note'))

def public_capacity():
    # Public pages describe intake as paused, with no limits, if the capacity row cannot be read.
    try:
        config=Capacity.objects.get(pk=1)
    except (Capacity.DoesNotExist,DatabaseError):
        return None,False
    return config,services.intake_accepting(config)

@require_GET
def home(request):
    config,accepting=public_capacity()
    return render(request,'archive/home.html',{'config':config,'intake_accepting':accepting})

@require_GET
def policies(request):
    # Public capacity disclosure: configured limits only. No queue occupancy or private record count is rendered.
    config,accepting=public_capacity()
    return render(request,'archive/policies.html',{'config':config,'intake_accepting':accepting,
        'field_limits':[(label,f'{Submission._meta.get_field(name).max_length:,}') for name,label in PUBLIC_FIELD_LIMITS],
        'body_kib':settings.DATA_UPLOAD_MAX_MEMORY_SIZE//1024,'artifact_links':MAX_ARTIFACT_LINKS})

def public_versions():
    # The latest published version only. No Submission or reputation field participates in discovery.
    # A correlated query avoids creating unbounded OR trees as the archive grows.
    from django.db.models import OuterRef,Subquery
    numbers=Version.objects.filter(work_id=OuterRef('work_id')).order_by('-number').values('number')[:1]
    return Version.objects.filter(work__withdrawn_at__isnull=True,number=Subquery(numbers)).select_related('work')

@require_GET
def browse(request):
    q=request.GET.get('q','').strip()
    if len(q)>100:
        return HttpResponse('Search is limited to 100 characters.',status=400)
    versions=public_versions()
    if q:
        versions=versions.filter(Q(snapshot__title__icontains=q)|Q(snapshot__abstract__icontains=q)|Q(snapshot__byline__icontains=q))
    return render(request,'archive/browse.html',{'versions':versions.order_by('-published_at','-id')[:50],'q':q})

@require_GET
def latest(request,work_id):
    version=Version.objects.filter(work_id=work_id).order_by('-number').first()
    if not version:
        raise Http404
    return redirect('version',work_id=work_id,number=version.number)

@require_GET
def version(request,work_id,number):
    row=get_object_or_404(Version.objects.select_related('work'),work_id=work_id,number=number)
    work=row.work
    versions=work.versions.order_by('number')
    # Tombstone context contains zero manuscript text, even for earlier versions.
    if work.withdrawn_at:
        row.snapshot={}
    return render(request,'archive/version.html',{'version':row,'work':work,'versions':versions,
        'is_author':request.user.is_authenticated and request.user.id==work.author_id,
        'citation':request.build_absolute_uri(reverse('version',args=[work.id,row.number]))})

@require_GET
def export_version(request,work_id,number):
    row=get_object_or_404(Version.objects.select_related('work'),work_id=work_id,number=number)
    data={'id':str(row.work_id),'version':row.number,'digest':row.digest,'published_at':row.published_at.isoformat()}
    if row.work.withdrawn_at:
        data.update(withdrawn=True,reason=row.work.withdrawal_reason)
    else:
        data['research']=row.snapshot
    return JsonResponse(data,json_dumps_params={'ensure_ascii':False})

@login_required
@require_GET
def dashboard(request):
    return render(request,'archive/dashboard.html',{'submissions':Submission.objects.filter(author=request.user).order_by('-updated_at')[:100]})

@login_required
@require_POST
def new_submission(request):
    try:
        row=services.create_submission(request.user)
    except services.WorkflowError as exc:
        return fail(request,exc)
    return redirect('edit',submission_id=row.id)

@login_required
@require_POST
def revision(request,work_id):
    try:
        row=services.create_submission(request.user,work_id)
    except services.WorkflowError as exc:
        return fail(request,exc)
    return redirect('edit',submission_id=row.id)

@login_required
@sensitive_post_parameters()
@require_http_methods(['GET','POST'])
def edit(request,submission_id):
    row=get_object_or_404(Submission,pk=submission_id,author=request.user)
    form=SubmissionForm(request.POST if request.method=='POST' else None,instance=row,initial={'revision':row.revision})
    context={'submission':row,'form':form,'editable':row.state in ['draft','changes'],
        'decisions':row.decisions.select_related('actor'),'appeals':row.appeals.all(),'appeal_form':ReasonForm() if row.state in ['changes','declined'] else None}
    if request.method=='POST':
        action=request.POST.get('action','save')
        if action not in ['save','submit']:
            return HttpResponse('Unknown action.',status=400)
        if form.is_valid():
            if action == 'submit':
                required=['title','byline','abstract','methods','claims','limitations','provenance','license','ai_disclosure','rights_confirmed','privacy_confirmed']
                if row.work_id:
                    required.append('change_note')
                for field in required:
                    if not form.cleaned_data.get(field):
                        form.add_error(field,'Complete this field before submitting. You can save an incomplete draft.')
                if form.errors:
                    return render(request,'archive/edit.html',context,status=400)
            data=dict(form.cleaned_data)
            expected=data.pop('revision')
            try:
                services.save_submission(request.user,row.id,data,expected,submit=action=='submit')
            except services.WorkflowError as exc:
                return fail(request,exc,'archive/edit.html',context)
            messages.success(request,'Saved and queued for human moderation.' if action=='submit' else 'Draft saved. You can resume it from your workspace.')
            return redirect('edit',submission_id=row.id)
        return render(request,'archive/edit.html',context,status=400)
    return render(request,'archive/edit.html',context)

@login_required
@require_GET
def export_submission(request,submission_id):
    row=get_object_or_404(Submission,pk=submission_id,author=request.user)
    return JsonResponse({'id':str(row.id),'state':row.state,'revision':row.revision,'research':row.payload(),
        'decisions':list(row.decisions.values('action','reason','revision','digest','created_at')),
        'appeals':list(row.appeals.values('reason','response','created_at','resolved_at'))},json_dumps_params={'ensure_ascii':False})

@moderator_required
@require_GET
def queue(request):
    return render(request,'archive/queue.html',{'submissions':Submission.objects.filter(state='submitted').order_by('submitted_at')[:20]})

@moderator_required
@sensitive_post_parameters()
@require_http_methods(['GET','POST'])
def moderate(request,submission_id):
    row=get_object_or_404(Submission,pk=submission_id)
    form=DecisionForm(request.POST if request.method=='POST' else None,initial={'revision':row.revision})
    context={'submission':row,'snapshot':row.frozen_snapshot,'form':form,'decisions':row.decisions.select_related('actor'), 'appeals':row.appeals.all()}
    if request.method=='POST':
        if not form.is_valid():
            return render(request,'archive/moderate.html',context,status=400)
        try:
            services.decide(request.user,row.id,form.cleaned_data['action'],form.cleaned_data['reason'],form.cleaned_data['revision'],conflicts=form.cleaned_data['conflicts'])
        except services.WorkflowError as exc:
            return fail(request,exc,'archive/moderate.html',context)
        messages.success(request,'Human moderation decision recorded.')
        return redirect('moderate',submission_id=row.id)
    return render(request,'archive/moderate.html',context)

@login_required
@sensitive_post_parameters()
@require_POST
def appeal(request,submission_id):
    form=ReasonForm(request.POST)
    if not form.is_valid():
        return HttpResponse('A reason of at most 2,000 characters is required.',status=400)
    try:
        services.appeal(request.user,submission_id,form.cleaned_data['reason'])
    except services.WorkflowError as exc:
        return fail(request,exc)
    messages.success(request,'Your appeal was recorded privately for human consideration.')
    return redirect('edit',submission_id=submission_id)

@moderator_required
@sensitive_post_parameters()
@require_POST
def resolve_appeal(request,appeal_id):
    form=ReasonForm(request.POST)
    if not form.is_valid():
        return HttpResponse('Provide a bounded response.',status=400)
    try:
        row=services.resolve_appeal(request.user,appeal_id,form.cleaned_data['reason'],request.POST.get('reopen')=='on')
    except services.WorkflowError as exc:
        return fail(request,exc)
    return redirect('moderate',submission_id=row.submission_id)

@login_required
@sensitive_post_parameters()
@require_http_methods(['GET','POST'])
def withdraw(request,work_id):
    work=get_object_or_404(Work,pk=work_id)
    if request.user.id != work.author_id and not services.is_moderator(request.user):
        raise Http404
    form=WithdrawalForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        try:
            services.withdraw(request.user,work_id,form.cleaned_data['reason'])
        except services.WorkflowError as exc:
            return fail(request,exc,'archive/withdraw.html',{'form':form,'work':work})
        return redirect('work',work_id=work_id)
    return render(request,'archive/withdraw.html',{'work':work,'form':form},status=400 if request.method=='POST' else 200)

@sensitive_post_parameters()
@require_http_methods(['GET','POST'])
def report(request,work_id):
    if not Version.objects.filter(work_id=work_id).exists():
        raise Http404
    form=ReasonForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        try:
            services.report(work_id,form.cleaned_data['reason'])
        except services.WorkflowError as exc:
            return fail(request,exc,'archive/report.html',{'form':form})
        messages.success(request,'Report received privately. No contact details are collected in this form.')
        return redirect('work',work_id=work_id)
    return render(request,'archive/report.html',{'form':form},status=400 if request.method=='POST' else 200)

@moderator_required
@sensitive_post_parameters()
@require_http_methods(['GET','POST'])
def operations(request):
    config=Capacity.objects.get(pk=1)
    form=CapacityForm(request.POST if request.method=='POST' else None,instance=config,initial={'revision':config.revision})
    oldest=Submission.objects.filter(state='submitted').order_by('submitted_at').values_list('submitted_at',flat=True).first()
    context={'config':config,'form':form,'reports':Report.objects.filter(resolved_at__isnull=True).order_by('created_at')[:100],
        'pending_appeals':Appeal.objects.filter(resolved_at__isnull=True).select_related('submission').order_by('created_at')[:100],
        'metrics':{'queued':Submission.objects.filter(state='submitted').count(),'oldest_queued_at':oldest,
            'drafts':Submission.objects.filter(state__in=['draft','changes']).count(),'published_versions':Version.objects.count(),
            'withdrawn':Work.objects.filter(withdrawn_at__isnull=False).count(),'open_reports':Report.objects.filter(resolved_at__isnull=True).count()}}
    if request.method=='POST':
        if form.is_valid():
            data=dict(form.cleaned_data)
            expected=data.pop('revision')
            reason=data.pop('reason')
            try:
                services.configure(request.user,data,expected,reason)
            except services.WorkflowError as exc:
                return fail(request,exc,'archive/operations.html',context)
            messages.success(request,'Capacity decision recorded.')
            return redirect('operations')
        return render(request,'archive/operations.html',context,status=400)
    return render(request,'archive/operations.html',context)

@moderator_required
@sensitive_post_parameters()
@require_POST
def report_resolve(request,report_id):
    form=ReasonForm(request.POST)
    if not form.is_valid():
        return HttpResponse('Provide a bounded response.',status=400)
    try:
        services.resolve_report(request.user,report_id,form.cleaned_data['reason'])
    except services.WorkflowError as exc:
        return fail(request,exc)
    return redirect('operations')

@require_GET
def health(request):
    try:
        Capacity.objects.only('id').get(pk=1)
    except (OperationalError,Capacity.DoesNotExist):
        return JsonResponse({'status':'unavailable'},status=503)
    return JsonResponse({'status':'ok'})
