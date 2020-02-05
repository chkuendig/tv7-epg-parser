# tv7-epg-parser


# public API:

 https://www.init7.net/en/support/faq/TV-andere-Geraete/:

```
wget https://api.init7.net/tvchannels.xspf
wget https://api.init7.net/tvchannels.m3u
```

# from Android TV app:
From `core/api/TvApiFactory.java`:
```
BASE_URL="https://tv7api2.tv.init7.net/api/"
```

From `core/api/TvApi.java`:
```
# @GET("allowed/")
#  Call<AllowedResponse# allowed();
curl "${BASE_URL}allowed/" # allowed.json
```

```
# @GET("epg/?now__lte=true&now__gte=true")
# Call<EPGListResponse# getCurrentEPG(@Query("channel") String paramString);
curl "${BASE_URL}/epg/?now__lte=true&now__gte=true" # getCurrentEPG.json
```

```
# @GET("epg/")
#  Call<EPGListResponse# getEPG(@Query("channel") String paramString);
 curl "${BASE_URL}epg/?channel=4c8a7d39-009d-4835-b6f9-69c7268fd9d4" # getEPG-channel.json
```

```  
#  @GET("epg/")
#  Call<EPGListResponse# getEPG(@Query("channel") String paramString1, @Query("limit") int paramInt1, @Query("offset") int paramInt2, @Header("If-None-Match") String paramString2);
```

```  
#  @GET("epg/")
#  Call<EPGListResponse# getEPG(@Query("channel") String paramString, @Query("limit") int paramInt, @Query("now__lte") boolean paramBoolean1, @Query("now__gte") boolean paramBoolean2);
```

```  
#  @GET("replay/")
#  Call replayData(String paramString, Date paramDate1, Date paramDate2);
```
# @GET("tvchannel/")
#  Call<TvChannelListResponse> tvChannelList();
curl "${BASE_URL}tvchannel/" > tvChannelList.json
```
# JSON Samples

get all epg titles for currently running
```
jq ".results[].title" getCurrentEPG.json 
```

show full channel list
```
jq '.results[] | "\(.ordernum) \(.name)"' tvChannelList.json | sort
```
 

show full channel list by change date
```
jq '.results[] | "\(.changed) \(.name)"' tvChannelList.json | sort
```
 