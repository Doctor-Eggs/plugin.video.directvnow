# -*- coding: utf-8 -*-
import requests
import routing
import logging
import json
import sys, os, xbmc, xbmcaddon
import cookielib
import urllib
import urlparse
from bs4 import BeautifulSoup
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent, addSortMethod, SORT_METHOD_LABEL

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()

@plugin.route('/')
def index():
    addDirectoryItem(plugin.handle, plugin.url_for(show_LiveTV), ListItem("Live TV"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(show_Networks), ListItem("Networks"), True)
    #addDirectoryItem(plugin.handle, plugin.url_for(show_Networks), ListItem("My Library"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(show_TVShowsMain), ListItem("TV Shows"), True)
    #addDirectoryItem(plugin.handle, plugin.url_for(show_Networks), ListItem("Movies"), True)
    #addDirectoryItem(plugin.handle, plugin.url_for(show_Networks), ListItem("Watch Now"), True)
    #addDirectoryItem(plugin.handle, plugin.url_for(show_Networks), ListItem("Discover"), True)
    
    endOfDirectory(plugin.handle)

@plugin.route('/LiveTV')
def show_LiveTV():
    url = 'https://api.cld.dtvce.com/discovery/metadata/channel/v3/service/allchannels?clientContext=&fisProperties=chlogo-clb-guide,56,42&sort=OrdCh=ASC'
    jsonKey = 'channelInfoList'
    json_source = get_JSON(url, jsonKey)
    
    for channel in json_source[jsonKey]:
        resourceId = channel['resourceId']
        channelName = channel['channelName']
        ccid = channel['ccid']
        channelImage = channel['imageList'][0]['imageUrl']
        li = ListItem(channelName)
        imageUrl = get_image(channel['imageList'][0])
        li.setArt({'icon': imageUrl, 'thumb': imageUrl})
        tempURL = 'http://download.tsi.telecom-paristech.fr/gpac/DASH_CONFORMANCE/TelecomParisTech/mp4-live/mp4-live-mpd-AV-BS.mpd'
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        li.setMimeType('application/dash+xml')
        li.setContentLookup(False)
        addDirectoryItem(handle=plugin.handle, url=tempURL, listitem=li)
    endOfDirectory(plugin.handle)
    
@plugin.route('/Networks')
def show_Networks():
    urlBase = 'https://api.cld.dtvce.com/discovery/collection/carousel/v1/service/carousels/generic?clientContext=proximity:outofhome,pkgCode:HBO%20Skinny_Live%20A%20Little_DVR%2020%20hours&pageReference=ExploreNetworkHomeReference&itemIndex=0&fisProperties=nwlogo-bwlb,120,90&itemCount=150&sectionId=106254%2332@@7a2e82fb-3b17-40dd-ad9c-9766680103d3@@107047%2311@@'
    
    url = '{0}{1}'.format(urlBase,'1')
    jsonKey = 'resources'
    json_source = get_JSON(url, jsonKey)
    for channel in json_source[jsonKey]:
        li = ListItem(channel['networkName'])
        imageUrl = get_image(channel['images'][0])
        li.setArt({'icon': imageUrl, 'thumb': imageUrl})
        
        addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Network, query='resourceId={0}'.format(channel['resourceId'])), listitem=li, isFolder=True)
        
    url = '{0}{1}'.format(urlBase,'2')
    jsonKey = 'resources'
    json_source = get_JSON(url, jsonKey)
    for channel in json_source[jsonKey]:
        li = ListItem(channel['networkName'])
        imageUrl = get_image(channel['images'][0])
        li.setArt({'icon': imageUrl, 'thumb': imageUrl})        
        addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Network, query='resourceId={0}'.format(channel['resourceId'])), listitem=li, isFolder=True)
    addSortMethod(plugin.handle, SORT_METHOD_LABEL)
    endOfDirectory(plugin.handle)
    
@plugin.route('/Networks/Network')
def show_Network():
    args = urlparse.parse_qs(plugin.args['query'][0])
    resourceId = args['resourceId'][0]
    addDirectoryItem(plugin.handle, plugin.url_for(show_Network, query="livetv=123"), ListItem("On Now"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(show_Network, query="livetv=123"), ListItem("TV Shows"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(show_Network, query="livetv=123"), ListItem("Movies"), True)
    
    url = 'https://api.cld.dtvce.com/discovery/metadata/network/v2/service/network/{0}?fisProperties=NET:nwlogo-bwdb,120,90%23CHA:chlogo-cdb-guide,56,42&clientContext=proximity:outofhome,pkgCode:HBO%20Skinny_Live%20A%20Little_DVR%2020%20hours'.format(resourceId)
    jsonKey = 'providers'
    json_source = get_JSON(url, jsonKey)
    #for networkCategory in json_source[jsonKey]:
    providerId=json_source[jsonKey][0]['resourceId']
    for category in json_source[jsonKey][0]['categories']:
        addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_NetworkCategory, query='networkCategory={0}&providerId={1}'.format(category,providerId)), listitem=ListItem(category), isFolder=True)
    endOfDirectory(plugin.handle)
    
@plugin.route('/Networks/NetworkCategory')
def show_NetworkCategory():
    args = urlparse.parse_qs(plugin.args['query'][0])
    networkCategory = args['networkCategory'][0]
    providerId = args['providerId'][0]
    
    url = 'https://api.cld.dtvce.com/discovery/metadata/network/v2/service/network/{0}/program?itemIndex=0&itemCount=15&fisProperties=poster,278,156&clientContext=proximity:outofhome,pkgCode:HBO%20Skinny_Live%20A%20Little_DVR%2020%20hours&providerId={0}&providerCategory={1}'.format(providerId,networkCategory)
    jsonKey = 'resources'
    json_source = get_JSON(url, jsonKey)
    for value in json_source[jsonKey]:
        li = ListItem(value['title'])
        imageUrl = get_image(value['images'][0])
        li.setArt({'icon': imageUrl, 'thumb': imageUrl})
        addDirectoryItem(handle=plugin.handle, url='', listitem=li, isFolder=True)
    endOfDirectory(plugin.handle)

@plugin.route('/TVShows')
def show_TVShowsMain():
    # TV Show genres
    url = 'https://api.cld.dtvce.com/discovery/metadata/genre/v1/service/genres?showType=show&clientContext='
    jsonKey = 'facets'
    
    json_source = get_JSON(url, jsonKey)
    
    for facet in json_source[jsonKey]:
        addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Genre, 'show', facet, '0'), listitem=ListItem('{0} Series'.format(facet)), isFolder=True)
    
    # Carousels of TV Show items:
    url = 'https://api.cld.dtvce.com/discovery/uiux/layout/v1/service/layouts/ExploreTVShowReference?clientContext=clientContext='
    jsonKey = 'page'
    
    json_source = get_JSON(url, jsonKey)
    
    for section in json_source[jsonKey]['sections']:
        for block in section['blocks']:
            sectionId = section['sectionId'].replace('#','%23')
            #xbmc.log(block)
            if 'blockType' in block:
                if block['blockType'] == 'LAYOUT':
                    addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Carousel, sectionId), listitem=ListItem(block['blockLabel'].title()), isFolder=True)
                #elif block['blockType'] == 'SEARCH':
                #    addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Genres, sectionId), listitem=ListItem(block['blockLabel']), isFolder=True)

    endOfDirectory(plugin.handle)

@plugin.route('/show_Carousel/<sectionId>')
def show_Carousel(sectionId):
    url='https://api.cld.dtvce.com/discovery/collection/carousel/v1/service/carousels/generic?clientContext=proximity:outofhome,dmaID:560_0,billingDmaID:560,regionID:BGTN4HD_BGTN3HD_BIG10HD_BG10O2H_FSCR3HD_FSPNC3H,zipCode:27608,countyCode:183,stateNumber:37,stateAbbr:NC,pkgCode:DVR%2020%20hours_Live%20A%20Little&sectionId={0}&pageReference=ExploreTVShowReference&itemIndex=0&fisProperties=poster-ni,278,156,dc&itemCount=30'.format(sectionId)
    jsonKey = 'resources'
    json_source = get_JSON(url,jsonKey)

    for item in json_source[jsonKey]:
        li = ListItem(item['title'])
        if 'images' in item:
            if 'imageId' in item['images'][0]:
                imgBase = 'https://dfwfis-sponsored.secure.footprint.net/catalog/image/imageserver/v1/service/series/{0}/iconic-ci/'.format(item['images'][0]['imageId'])
                li.setArt({'icon': '{0}{1}/{2}'.format(imgBase,278,156), 'thumb': '{0}{1}/{2}'.format(imgBase,640,360), 'fanart': '{0}{1}/{2}'.format(imgBase,1280,720)})
                li.setInfo(type="Video", infoLabels={"Title": item['title'], 'plot': item['description']})
            #https://dfwfis-sponsored.secure.footprint.net/catalog/image/imageserver/v1/service/series/SH015697930000/iconic-ci/1280/720
        addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Series, query='sectionId={0}'.format(item['resourceId'])), listitem=li, isFolder=True)
    endOfDirectory(plugin.handle)
    
@plugin.route('/<showType>/Genre/<genre>/<pageNumber>')
def show_Genre(showType,genre,pageNumber):
    showsPerPage = 30
    itemIndex=int(pageNumber) * showsPerPage
    url='https://api.cld.dtvce.com/discovery/metadata/genre/v1/service/genres/{0}/programs?itemIndex={1}&itemCount={2}&showType={3}&fisProperties=poster-ni,340,191,dc&clientContext='.format(genre,itemIndex,showsPerPage,showType)
    jsonKey='resources'
    json_source = get_JSON(url,jsonKey)
    
    totalShows = json_source['estimatedMatches']

    if showType == 'shows':
        setContent(plugin.handle, 'tvshows')
    for item in json_source[jsonKey]:
        li = ListItem(item['title'])
        imageUrl = get_image(item['images'][0])
        li.setArt({'icon': imageUrl, 'thumb': imageUrl})
        addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Series, query='sectionId={0}'.format(item['resourceId'])), listitem=li, isFolder=True)
    
    currentPage = int(pageNumber) + 1
    totalPages = (totalShows // showsPerPage) + 1
    nextPage = currentPage + 1
    prevPage = currentPage - 1
    nextFive = currentPage + 5
    prevFive = currentPage - 5
    if nextPage > totalPages:
        nextPage = 1
    if prevPage < 1:
        prevPage = totalPages
    if nextFive > totalPages:
        nextFive = nextFive - totalPages
    if prevFive < 1:
        prevFive = prevFive + totalPages
    
    addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Genre, 'show', genre, nextPage - 1), listitem=ListItem('Next: Page {0}'.format(nextPage)), isFolder=True)
    addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Genre, 'show', genre, prevPage - 1), listitem=ListItem('Previous: Page {0}'.format(prevPage)), isFolder=True)
    addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Genre, 'show', genre, nextFive - 1), listitem=ListItem('Forward 5 Pages: Page {0}'.format(nextFive)), isFolder=True)
    addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Genre, 'show', genre, prevFive - 1), listitem=ListItem('Back 5 Pages: Page {0}'.format(prevFive)), isFolder=True)
    
    endOfDirectory(plugin.handle)
    
@plugin.route('/TVShows/Series')
def show_Series():
    args = urlparse.parse_qs(plugin.args['query'][0])
    seriesId = args['sectionId'][0]
    url='https://api.cld.dtvce.com/discovery/metadata/series/v2/service/details/VIDEO_CONTENT/{0}?clientContext=&fisProperties=iconic-ci,640,360,dc'.format(seriesId)
    jsonKey = 'seasons'
    json_source = get_JSON(url,jsonKey)
    
    for image in json_source['images']:
        imgBase = 'https://dfwfis-sponsored.secure.footprint.net/catalog/image/imageserver/v1/service/series/{0}/iconic-ci/'.format(image['imageId'])
    
    for season in json_source[jsonKey]:
        li = ListItem('Season {0}'.format(season['seasonNumber']))
        li.setArt({'icon': '{0}{1}/{2}'.format(imgBase,278,156), 'thumb': '{0}{1}/{2}'.format(imgBase,640,360), 'fanart': '{0}{1}/{2}'.format(imgBase,1280,720)})
        addDirectoryItem(handle=plugin.handle, url=plugin.url_for(show_Episodes, query='seriesId={0}&seasonNum={1}&indexValue=0'.format(seriesId,season['seasonNumber'])), listitem=li, isFolder=True)
    setContent(plugin.handle, 'seasons')
    endOfDirectory(plugin.handle)

@plugin.route('/TVShows/Season')
def show_Episodes():
    args = urlparse.parse_qs(plugin.args['query'][0])
    seriesId = args['seriesId'][0]
    seasonNum = args['seasonNum'][0]
    indexValue = args['indexValue'][0]

    add_Episodes(seriesId,seasonNum,indexValue)

    setContent(plugin.handle, 'episodes')
    endOfDirectory(plugin.handle)
       
def add_Episodes(seriesId,seasonNum,indexValue):
    itemCount=12
    itemIndex=int(indexValue) * itemCount
    url='https://api.cld.dtvce.com/discovery/metadata/series/v2/service/episodes?clientContext=proximity:outofhome,pkgCode:DVR%2020%20hours_HBO%20Skinny_Live%20A%20Little&resourceId={0}&fisProperties=keyframe-ci,340,191,dc%23bg-player,820,461%23bg-fplayer,1920,1080%23PRO:logo-player,110,83%23PRO:logo-fplayer,110,83%23CHA:logo-player,110,83%23CHA:logo-fplayer,110,83&seasonList={1}&itemIndex={2}&itemCount={3}&latestSeason=true'.format(seriesId,seasonNum,itemIndex,itemCount)
    jsonKey = 'season'
    json_source = get_JSON(url,jsonKey)
    
    for episode in json_source[jsonKey]['contents']:
        if episode['contentType'] == 'EPISODE':
            try:
                li = ListItem('{0}. {1}'.format(str(episode['episodeNumber']).zfill(2),episode['episodeTitle'].encode('utf-8')))
            except:
                try:
                    li = ListItem(episode['episodeTitle'].encode('utf-8'))
                except:
                    li = ListItem('?????')
                    pass
                pass
            imgIcon = 'https://dfwfis-sponsored.secure.footprint.net/catalog/image/imageserver/v1/service/episode/default/keyframe-ci/340/191'
             
            imageUrl = get_image(episode['images'][0])
            li.setArt({'icon': imageUrl, 'thumb': imageUrl})
            try:
                imgFanart = 'https://dfwfis-sponsored.secure.footprint.net/catalog/image/imageserver/v1/service/series/{0}/iconic-ci/{1}/{2}'.format(episode['tmsConnectorId'],1280,720)
            except:
                imgFanart = imgThumb
            info={
                'mediatype':'episode',
                'plot': episode['description'],
                'tvshowtitle': episode['title'],
                'label': episode['episodeTitle'].encode('utf-8'),
                'title': episode['episodeTitle'].encode('utf-8'),
                'originaltitle': episode['episodeTitle'].encode('utf-8'),
                'genre': 'Comedy',
                'aired': episode['originalAirDate'],
                'duration': episode['consumables'][0]['duration'],
                'season': episode['seasonNumber'],
                'episode': episode['episodeNumber'],
                'mpaa': episode['parentalRating']
            }
            li.setInfo(type="Video", infoLabels=info)
            li.setArt({'icon': imageUrl, 'thumb': imageUrl, 'fanart': imgFanart})
            li.setProperty("IsPlayable","true")
            li.setProperty("IsInternetStream","true")
            tempURL = 'http://download.tsi.telecom-paristech.fr/gpac/DASH_CONFORMANCE/TelecomParisTech/mp4-live/mp4-live-mpd-AV-BS.mpd'
            li.setProperty('inputstreamaddon', 'inputstream.adaptive')
            li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            li.setMimeType('application/dash+xml')
            li.setContentLookup(False)
            addDirectoryItem(handle=plugin.handle, url=tempURL, listitem=li)
            
    if json_source['hasMore'] == True:
        add_Episodes(seriesId,seasonNum,int(indexValue)+1)
    
def get_JSON(urlValue, jsonKey):
    url=urlValue
    header = {
        'Host': 'api.cld.dtvce.com',
        'Connection': 'keep-alive',
        'app-build': 'DFW Web571/2.0.0/development',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {0}'.format(ADDON.getSetting('accessToken')),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    r = requests.get(url, headers=header, cookies=load_cookies())

    json_source = r.json()
    if not jsonKey in json_source:
        json_source = setTokens(url)
    return json_source

    
def get_image(imgStruct):
    if 'imageUrl' in imgStruct:
        imageUrl = imgStruct['imageUrl']
    else:
        imageUrl = imgStruct['defaultImageUrl']
    return imageUrl
    
def setTokens(urlValue):
    url = 'https://cprodmasx.att.com/commonLogin/igate_wam/multiLogin.do'
    payload = {
        'userid': ADDON.getSetting('username'),
        'password': ADDON.getSetting('password'),
        'cancelURL': 'https://cprodmasx.att.com/commonLogin/igate_wam/controller.do?TAM_OP=login&USERNAME=unauthenticated&ERROR_CODE=0x00000000&ERROR_TEXT=HPDBA0521I%20%20%20Successful%20completion&METHOD=GET&URL=%2Fpkmsvouchfor%3FATT%26https%3A%2F%2Fcprodx.att.com%2FTokenService%2FnxsATS%2FWATokenService%3FisPassive%3Dfalse%26appID%3Dm14961%26lang%3Den%26returnURL%3Dhttps%253A%252F%252Fprod-dfw-ums.quickplay.com%252Fdfw%252Fums%252Fv1%252Flogin%253FnextUrl%253Dhttps%25253A%25252F%25252Fwww.directvnow.com%25252Faccounts%25252Fsign-in&REFERER=https%3A%2F%2Fcprodmasx.att.com%2FcommonLogin%2Figate_wam%2Fcontroller.do%3FTAM_OP%3Dlogout%26USERNAME%3D%26ERROR_CODE%3D0x00000000%26ERROR_TEXT%3DSuccessful%2520completion%26METHOD%3DGET%26URL%3D%2Fpkmslogout%26REFERER%3D%26AUTHNLEVEL%3D%26FAILREASON%3D%26OLDSESSION%3D%26style%3DTokenService%26returnurl%3Dhttps%253A%252F%252Fcprodx.att.com%252FTokenService%252FnxsATS%252FWATokenService%253FisPassive%253Dfalse%2526appID%253Dm14961%2526lang%253Den%2526returnURL%253Dhttps%25253A%25252F%25252Fprod-dfw-ums.quickplay.com%25252Fdfw%25252Fums%25252Fv1%25252Flogin%25253FnextUrl%25253Dhttps%2525253A%2525252F%2525252Fwww.directvnow.com%2525252Faccounts%2525252Fsign-in&HOSTNAME=cprodmasx.att.com&AUTHNLEVEL=&FAILREASON=&OLDSESSION=',
        'remember_me': 'N',
        'source': 'm14961',
        'loginURL': '/WEB-INF/pages/directvNow/dtvNowLoginWeb.jsp',
        'targetURL': '/pkmsvouchfor?ATT&https://cprodx.att.com/TokenService/nxsATS/WATokenService?isPassive=false&appID=m14961&lang=en&returnURL=https%3A%2F%2Fapi.cld.dtvce.com%2Faccount%2Faeg%2Fums%2Ftglogin%3FnextUrl%3Dhttps%253A%252F%252Fwww.directvnow.com%252Faccounts%252Fsign-in',
        'appID': 'm14961',
        'HOSTNAME': 'cprodmasx.att.com',
        'style': 'm14961'
    }
    r = requests.post(url, data=payload)

    save_cookies(r.cookies)

    soup = BeautifulSoup(r.content, 'html.parser')
    formAction = soup.find('form').get('action')
    formTokenId = soup.find('input', {'name':'TATS-TokenID'}).get('value')

    url=formAction
    header = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9'
    }
    payload = {
    'TATS-TokenID':	formTokenId
    }
    r = requests.post(url, headers=header, data=payload)

    nonceVar=r.url.split('=')
    urlReferrer=r.url

    url='https://api.cld.dtvce.com/account/aeg/ums/getSessionForToken?apiKey=qwerty'
    header = {
        'Referer': urlReferrer,
        'Host': 'api.cld.dtvce.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': '*',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'Keep-Alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko;',
        'Cache-Control': 'no-cache',
        'Origin': 'https://www.directvnow.com'
    }
    payload = '{{"nonce":"{0}"}}'.format(nonceVar[1])
    r = requests.post(url, headers=header, data=payload)

    tToken = 'failed'

    json_source = r.json()
    if 'data' in json_source:
        if 'cacheResponse' in json_source['data']:
            if 'tToken' in json_source['data']['cacheResponse']:
                tToken = json_source['data']['cacheResponse']['tToken']
    travellingSession = 'failed'
    if 'data' in json_source:
        if 'session' in json_source['data']:
            if 'travellingSession' in json_source['data']['session']:
                travellingSession = json_source['data']['session']['travellingSession']

    url='https://www.directvnow.com/auth/checkToken'
    header = {
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko;',
        'Connection': 'Close',
        'Host': 'www.directvnow.com'
    }
    payload = {
        'tToken': tToken
    }
    r = requests.get(url, headers=header, params=payload)
    accessToken = 'failed'
    for myCookie in r.cookies:
        if myCookie.name == 'accessToken':
            accessToken = urllib.unquote_plus(myCookie.value)
    
    ADDON.setSetting(id='accessToken',value=accessToken)

    save_cookies(r.cookies)
    header = {
        'Host': 'api.cld.dtvce.com',
        'Connection': 'keep-alive',
        'app-build': 'DFW Web571/2.0.0/development',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {0}'.format(ADDON.getSetting('accessToken')),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    r = requests.get(url=urlValue, headers=header, cookies=load_cookies())
    json_source = r.json()
    return json_source

def save_cookies(cookiejar):
    addon_profile_path = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    cookie_file = os.path.join(addon_profile_path, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file,ignore_discard=True)
    except:
        pass
    for c in cookiejar:
        args = dict(vars(c).items())
        args['rest'] = args['_rest']
        del args['_rest']
        c = cookielib.Cookie(**args)
        cj.set_cookie(c)
    cj.save(cookie_file, ignore_discard=True)

def load_cookies():
    addon_profile_path = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    cookie_file = os.path.join(addon_profile_path, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass

    return cj

def run():
    plugin.run()
