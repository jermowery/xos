#views.py
import os
import sys
from django.views.generic import TemplateView, View
import datetime
from pprint import pprint
import json
from core.models import *
from django.http import HttpResponse
from django.core import urlresolvers
import traceback
import socket

if os.path.exists("/home/smbaker/projects/vicci/cdn/bigquery"):
    sys.path.append("/home/smbaker/projects/vicci/cdn/bigquery")
else:
    sys.path.append("/opt/planetstack/hpc_wizard")
import hpc_wizard
from planetstack_analytics import DoPlanetStackAnalytics

class DashboardWelcomeView(TemplateView):
    template_name = 'admin/dashboard/welcome.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        userDetails = getUserSliceInfo(request.user)
        #context['site'] = userDetails['site']

        context['userSliceInfo'] = userDetails['userSliceInfo']
        context['cdnData'] = userDetails['cdnData']
        return self.render_to_response(context=context)

def getUserSliceInfo(user, tableFormat = False):
        userDetails = {}
#        try:
# //           site = Site.objects.filter(id=user.site.id)
#  //      except:
#   //         site = Site.objects.filter(name="Princeton")
#    //    userDetails['sitename'] = site[0].name
#     //   userDetails['siteid'] = site[0].id

        userSliceData = getSliceInfo(user)
        if (tableFormat):
#            pprint("*******      GET USER SLICE INFO")
            userDetails['userSliceInfo'] = userSliceTableFormatter(userSliceData)
        else:
            userDetails['userSliceInfo'] = userSliceData
        userDetails['cdnData'] = getCDNOperatorData();
#        pprint( userDetails)
        return userDetails

class TenantCreateSlice(View):
    def post(self, request, *args, **kwargs):
        sliceName = request.POST.get("sliceName", "0")
        serviceClass = request.POST.get("serviceClass", "0")
        imageName = request.POST.get("imageName", "0")
        actionToDo = request.POST.get("actionToDo", "0")
        print sliceName
        if (actionToDo == "add"):
           serviceClass = ServiceClass.objects.get(name=serviceClass)
           site = request.user.site
           #image = Image.objects.get(name=imageName)
           newSlice = Slice(name=sliceName,serviceClass=serviceClass,site=site,imagePreference=imageName)
           newSlice.save()
        return newSlice


def getTenantSliceInfo(user, tableFormat = False):
    tenantSliceDetails = {}
    tenantSliceData = getTenantInfo(user)
    tenantServiceClassData = getServiceClassInfo(user)
    if (tableFormat):
       tenantSliceDetails['userSliceInfo'] = userSliceTableFormatter(tenantSliceData)
       tenantSliceDetails['sliceServiceClass']=userSliceTableFormatter(tenantServiceClassData)
    else:
       tenantSliceDetails['userSliceInfo'] = tenantSliceData
    tenantSliceDetails['sliceServiceClass']=userSliceTableFormatter(tenantServiceClassData)
    tenantSliceDetails['image']=userSliceTableFormatter(getImageInfo(user))
    tenantSliceDetails['network']=userSliceTableFormatter(getNetworkInfo(user))
    tenantSliceDetails['deploymentSites']=userSliceTableFormatter(getDeploymentSites())
    tenantSliceDetails['sites'] = userSliceTableFormatter(getTenantSitesInfo());
    return tenantSliceDetails


def getTenantInfo(user):
    slices =Slice.objects.all()
    userSliceInfo = []
    for entry in slices:
       sliceName = Slice.objects.get(id=entry.id).name
       slice = Slice.objects.get(name=Slice.objects.get(id=entry.id).name)
       sliceServiceClass = entry.serviceClass.name
       preferredImage =  entry.imagePreference
       numSliver = 0
       sliceImage=""
       sliceSite = {}
       for sliver in slice.slivers.all():
            numSliver +=sliver.numberCores
           # sliceSite[sliver.deploymentNetwork.name] =sliceSite.get(sliver.deploymentNetwork.name,0) + 1
            sliceSite[sliver.node.site.name] = sliceSite.get(sliver.node.site.name,0) + 1
	    sliceImage = sliver.image.name
       userSliceInfo.append({'sliceName': sliceName,'sliceServiceClass': sliceServiceClass,'preferredImage':preferredImage, 'sliceSite':sliceSite,'sliceImage':sliceImage,'numOfSlivers':numSliver})
    return userSliceInfo

def getTenantSitesInfo():
	tenantSiteInfo=[]
        for entry in Site.objects.all():
		tenantSiteInfo.append({'siteName':entry.name})
	return tenantSiteInfo

def userSliceTableFormatter(data):
#    pprint(data)
    formattedData = {
                     'rows' : data
                    }
    return formattedData

def getServiceClassInfo(user):
    serviceClassList = ServiceClass.objects.all()
    sliceInfo = []
    for entry in serviceClassList:
          sliceInfo.append({'serviceClass':entry.name})
    return sliceInfo

def getImageInfo(user):
    imageList = Image.objects.all()
    imageInfo = []
    for imageEntry in imageList:
          imageInfo.append({'Image':imageEntry.name})
    return imageInfo

def getNetworkInfo(user):
   #networkList = Network.objects.all()
    networkList = ['Private Only','Private and Publicly Routable']
    networkInfo = []
    for networkEntry in networkList:
          #networkInfo.append({'Network':networkEntry.name})
          networkInfo.append({'Network':networkEntry})
    return networkInfo

def getDeploymentSites():
    deploymentList = Deployment.objects.all()
    deploymentInfo = []
    for entry in deploymentList:
        deploymentInfo.append({'DeploymentSite':entry.name})
    return deploymentInfo

def getSliceInfo(user):
    sliceList = Slice.objects.all()
    slicePrivs = SlicePrivilege.objects.filter(user=user)
    userSliceInfo = []
    for entry in slicePrivs:

        slicename = Slice.objects.get(id=entry.slice.id).name
        slice = Slice.objects.get(name=Slice.objects.get(id=entry.slice.id).name)
        sliverList=Sliver.objects.all()
        sites_used = {}
        for sliver in slice.slivers.all():
             #sites_used['deploymentSites'] = sliver.node.deployment.name
             # sites_used[sliver.image.name] = sliver.image.name
             sites_used[sliver.node.site.name] = sliver.numberCores
        sliceid = Slice.objects.get(id=entry.slice.id).id
        try:
            sliverList = Sliver.objects.filter(slice=entry.slice.id)
            siteList = {}
            for x in sliverList:
               if x.node.site not in siteList:
                  siteList[x.node.site] = 1
            slivercount = len(sliverList)
            sitecount = len(siteList)
        except:
            traceback.print_exc()
            slivercount = 0
            sitecount = 0

        userSliceInfo.append({'slicename': slicename, 'sliceid':sliceid,
                              'sitesUsed':sites_used,
                              'role': SliceRole.objects.get(id=entry.role.id).role,
                              'slivercount': slivercount,
                              'sitecount':sitecount})

    return userSliceInfo

def getCDNOperatorData(randomizeData = False):
    return hpc_wizard.get_hpc_wizard().get_sites_for_view()

def getPageSummary(request):
    slice = request.GET.get('slice', None)
    site = request.GET.get('site', None)
    node = request.GET.get('node', None)


class SimulatorView(View):
    def get(self, request, **kwargs):
        sim = json.loads(file("/tmp/simulator.json","r").read())
        text = "<html><head></head><body>"
        text += "Iteration: %d<br>" % sim["iteration"]
        text += "Elapsed since report %d<br><br>" % sim["elapsed_since_report"]
        text += "<table border=1>"
        text += "<tr><th>site</th><th>trend</th><th>weight</th><th>bytes_sent</th><th>hot</th></tr>"
        for site in sim["site_load"].values():
            text += "<tr>"
            text += "<td>%s</td><td>%0.2f</td><td>%0.2f</td><td>%d</td><td>%0.2f</td>" % \
                        (site["name"], site["trend"], site["weight"], site["bytes_sent"], site["load_frac"])
            text += "</tr>"
        text += "</table>"
        text += "</body></html>"
        return HttpResponse(text)

class DashboardUserSiteView(View):
    def get(self, request, **kwargs):
        return HttpResponse(json.dumps(getUserSliceInfo(request.user, True)), mimetype='application/javascript')

class TenantViewData(View):
    def get(self, request, **kwargs):
        return HttpResponse(json.dumps(getTenantSliceInfo(request.user, True)), mimetype='application/javascript')

def tenant_increase_slivers(user, siteName, slice, count):
        site = Site.objects.filter(name=siteName)
	nodes = Node.objects.filter(site=site)
	print nodes
	site.usedNodes = []
        site.freeNodes = []
	sliceName = Slice.objects.get(name=slice)
        for node in nodes:
            usedNode = False
            for sliver in node.slivers.all():
                if sliver in Sliver.objects.filter(slice=sliceName):
                    usedNode = True
            if usedNode:
                site.usedNodes.append(node)
		print site.usedNodes
            else:
                site.freeNodes.append(node)
	    print site
  	    slices =Slice.objects.all()
	    sliceName = Slice.objects.get(name=slice)
	    test = Sliver.objects.filter(slice=sliceName)
	    while (len(site.freeNodes) > 0) and (count > 0):
             	node = site.freeNodes.pop()
            	hostname = node.name
            	sliver = Sliver(name=node.name,
                            slice=sliceName,
                            node=node,
                            image = Image.objects.all()[0],
                            creator = User.objects.get(email=user),
                            deploymentNetwork=node.deployment,
                            numberCores =1 )
            	sliver.save()

            	print "created sliver", sliver
	    	print sliver.node
            	print sliver.numberCores
	    	site.usedNodes.append(node)
	    	count = int(count) - 1

def tenant_decrease_slivers(user, siteName, slice, count):
        site = Site.objects.filter(name=siteName)
        nodes = Node.objects.filter(site=site)
        slices = Slice.objects.all()
	site.usedNodes = []
        site.freeNodes = []
        sliceName = Slice.objects.get(name=slice)

	for node in nodes:
            usedNode = False
            for sliver in node.slivers.all():
                if sliver in Sliver.objects.filter(slice=sliceName):
                    usedNode = True
            if usedNode:
                site.usedNodes.append(node)
            else:
                site.freeNodes.append(node)
            print "used nodes", site.usedNodes
            slices =Slice.objects.all()
            sliceName = Slice.objects.get(name=slice)
            test = Sliver.objects.filter(slice=sliceName)
            while (count > 0):
                node = site.usedNodes.pop()
		print node
		print count
		for sliver in node.slivers.all():	
			if sliver.slice in slices:
                     		print "deleting sliver", sliver.slice
                     		sliver.delete()
            	site.freeNodes.append(node)
            	count = int(count) - 1
                print "deleted sliver", sliver

class TenantAddOrRemoveSliverView(View):
    def post(self, request, *args, **kwargs):
        siteName = request.POST.get("siteName", "0")
        actionToDo = request.POST.get("actionToDo", "0")
        count = request.POST.get("count","0")
	slice = request.POST.get("slice","0")

        if (actionToDo == "add"):
            tenant_increase_slivers(request.user, siteName,slice, count)
        elif (actionToDo == "rem"):
            tenant_decrease_slivers(request.user,siteName,slice, count)
        return HttpResponse('This is POST request ')

class DashboardSummaryAjaxView(View):
    def get(self, request, **kwargs):
        return HttpResponse(json.dumps(hpc_wizard.get_hpc_wizard().get_summary_for_view()), mimetype='application/javascript')

class DashboardAddOrRemoveSliverView(View):
    def post(self, request, *args, **kwargs):
        siteName = request.POST.get("site", "0")
        actionToDo = request.POST.get("actionToDo", "0")

        if (actionToDo == "add"):
            hpc_wizard.get_hpc_wizard().increase_slivers(siteName, 1)
        elif (actionToDo == "rem"):
            hpc_wizard.get_hpc_wizard().decrease_slivers(siteName, 1)

        print '*' * 50
        print 'Ask for site: ' + siteName + ' to ' + actionToDo + ' another HPC Sliver'
        return HttpResponse('This is POST request ')

class DashboardAjaxView(View):
    def get(self, request, **kwargs):
        return HttpResponse(json.dumps(getCDNOperatorData(True)), mimetype='application/javascript')

class DashboardAnalyticsAjaxView(View):
    def get(self, request, name="hello_world", **kwargs):
        if (name == "hpcSummary"):
            return HttpResponse(json.dumps(hpc_wizard.get_hpc_wizard().get_summary_for_view()), mimetype='application/javascript')
        elif (name == "hpcUserSite"):
            return HttpResponse(json.dumps(getUserSliceInfo(request.user, True)), mimetype='application/javascript')
        elif (name == "hpcMap"):
            return HttpResponse(json.dumps(getCDNOperatorData(True)), mimetype='application/javascript')
        elif (name == "bigquery"):
            (mimetype, data) = DoPlanetStackAnalytics(request)
            return HttpResponse(data, mimetype=mimetype)
        else:
            return HttpResponse(json.dumps("Unknown"), mimetype='application/javascript')

