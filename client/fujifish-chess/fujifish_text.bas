'' minimal example
''
'' @author Greg Gallard,  Borrows heavily from Eric Carr's 5card.bas
'' @email greggallardo at gmail dot com
'' @license gpl v. 3
'

? "FUJIFISH TEXT CLIENT TEST"

' FujiNet AppKey settings. These should not be changed
AK_LOBBY_CREATOR_ID = 1     ' FUJINET Lobby
AK_LOBBY_APP_ID  = 1        ' Lobby Enabled Game
AK_LOBBY_KEY_USERNAME = 0   ' Lobby Username key
AK_LOBBY_KEY_SERVER = 7     ' 

' my AppKey
AK_CREATOR_ID = $5364       ' creator id
AK_APP_ID = 2               ' chess
AK_KEY_SHOWHELP = 0         ' Shown help

DATA NAppKeyBlock()=0,0,0

' Read server endpoint stored from Lobby
serverEndpoint$="NA"
query$="NA"

Dim activePlayer, board$, message$
dim errorCount

' IMPORTANT  in C common  welcomActionVerifyServerDetails() calls
'read_appkey(AK_LOBBY_CREATOR_ID, AK_LOBBY_APP_ID, AK_LOBBY_KEY_SERVER, tempBuffer);
@NReadAppKey AK_LOBBY_CREATOR_ID, AK_LOBBY_APP_ID, AK_LOBBY_KEY_SERVER, &serverEndpoint$

' Parse endpoint url into server and query
if serverEndpoint$<>""
  for i=1 to len(serverEndpoint$)
    if serverEndpoint$[i,1]="?"
      query$=serverEndpoint$[i]
      serverEndpoint$=serverEndpoint$[1,i-1]
      exit
    endif
  next
else
  ' Default to known server if not specified by lobby. Override for local testing
  serverEndpoint$="http://10.25.50.61:8080/"
  'serverEndpoint$="http://192.168.2.41:8080/"
  'query$="?table=dev7"
endif

poke 65,0

? serverEndpoint$
? query$

dim responseBuffer(1023) BYTE
dim requestedMove$
dim player_name$(7), player_move$(7)
myName$ = ""





' ============================================================================
' (N AppKey Helpers) Call NRead/WriteAppKey to read or write app key

PROC __NOpenAppKey __N_creator __N_app __N_key __N_mode
  dpoke &NAppKeyBlock, __N_creator
  poke &NAppKeyBlock + 2, __N_app
  poke &NAppKeyBlock + 3, __N_key
  poke &NAppKeyBlock + 4, __N_mode
  SIO $70, 1, $DC, $80, &NAppKeyBlock, $09, 6, 0,0
ENDPROC

PROC NWriteAppKey __N_creator __N_app __N_key __N_string
  @__NOpenAppKey __N_creator, __N_app, __N_key, 1
  SIO $70, 1, $DE, $80, __N_string+1, $09, 64, peek(__N_string), 0
ENDPROC

PROC NReadAppKey __N_creator __N_app __N_key __N_string
  @__NOpenAppKey __N_creator, __N_app, __N_key, 0
  SIO $70, 1, $DD, $40, __N_string, $01, 66,0, 0
  MOVE __N_string+2, __N_string+1,64
  ' /\ MOVE - The first two bytes are the LO/HI length of the result. Since only the
  ' first byte is meaningful (length<=64), and since FastBasic string
  ' length is one byte, we just shift the entire string left 1 byte to
  ' overwrite the unused HI byte and instantly make it a string!
ENDPROC

' ============================================================================
' (N Helper) Gets the entire response from the specified unit into the provided buffer index for NInput to read from.
' WARNING! No check is made for buffer length. A more complete implimentation would handle that.
PROC NInputInit __NI_unit __NI_index
  __NI_bufferEnd = __NI_index + DPEEK($02EA)
  NGET __NI_unit, __NI_index, __NI_bufferEnd - __NI_index
ENDPROC



' ============================================================================
' (N Helper) Reads a line of text into the specified string - Similar to Atari BASIC: INPUT #N, MyString$
PROC NInput __NI_stringPointer

  ' Start the indexStop at the current index position
  __NI_indexStop = __NI_index

  ' Seek the end of this line (or buffer)
  while peek(__NI_indexStop) <> $9B and __NI_indexStop < __NI_bufferEnd
    inc __NI_indexStop
  wend

  ' Calculate the length of this result
  __NI_resultLen = __NI_indexStop - __NI_index

  ' Update the length in the output string
  poke __NI_stringPointer, __NI_resultLen

  ' If we successfully read a value, copy from the buffer to the string that was passed in and increment the index
  if __NI_indexStop < __NI_bufferEnd
    move __NI_index, __NI_stringPointer+1, __NI_resultLen

    ' Move the buffer index for the next input
    __NI_index = __NI_indexStop + 1
  endif
ENDPROC


' ============================================================================
' (Utility Functions) Convert string to upper case, replace character in string
PROC ToUpper text
  for __i=text+1 to text + peek(text)
    if peek(__i) >$60 and peek(__i)<$7B then poke __i, peek(__i)-32
  next
ENDPROC


' read players name from app key
' IMPORTANT  in C common  welcomActionVerifyPlayerName() calls
'read_appkey(AK_LOBBY_CREATOR_ID, AK_LOBBY_APP_ID, AK_LOBBY_KEY_USERNAME, tempBuffer);
@NReadAppKey AK_LOBBY_CREATOR_ID, AK_LOBBY_APP_ID, AK_LOBBY_KEY_USERNAME, &myName$
@ToUpper(&myName$)
? myName$
query$ =+ "&player="
query$ =+ myName$



' ============================================================================
' Handles connection errors - silently retries first, then eventually stops, requiring a key press to proceed
PROC SetError text
  inc errorCount                                                                           
  ' Expect occasional failure. Retry silently the first time
  if errorCount=1 then exit

  if errorCount<7
    PRINT "CONNECTING TO SERVER z"
    exit
  endif

  temp$=$(text)
  PRINT temp$

  GET K

  ' After key press, set errorCount back to 3 to display connecting message
  errorCount=3

ENDPROC


' ============================================================================
' Updates the state from the current Api call
PROC UpdateState

 ' Query Json response
 pause
 SIO $71, 8, $51, $80, &"N:"$9B+1, $1f, 256, 12, 0

 ' Check for query success
 pause
 NSTATUS 8
 IF PEEK($02ED) > 128
  @SetError &"COULD NOT CONNECT TO SERVER"
  EXIT
 ENDIF

' Initialize reading the api response
 @NInputInit 8, &responseBuffer

 ' Load state by looping through result and extracting each string at each EOL character
 isKey=1:inArray=0:playerCount=0:validMoveCount=0
 line$=""
 parent$=""

 do
  ' Get the next line of text from the api response
  @NInput &line$

  ' The response is mostly alternating lines of key and value, with the exception of arrays,
  ' which are handled as a special case further below.
  if isKey

    ' An empty key means we reached the end of the response
    if len(line$) = 0 then exit

    key$= line$
    ' Special case - "players" and "validMoves" keys are arrays of key/value pairs
    if key$="players" or key$="NULL"

      ' If the key is a NULL object, we effectively break out of the array by setting parent to empty
      if key$="NULL" then key$=""

      parent$=key$

      ' Reset isKey since the next line will be a key
      isKey = 0
    endif
  else
    value$ = line$
    ' Player struct
    if parent$="players"
      if key$="name"   ' name
        @ToUpper &value$
        if len(value$)>8 then value$=value$[1,8]
        player_name$(playerCount) = value$
      elif key$="m"   : player_move$(playerCount) = value$   ' move
      else
        parent$=""
      endif
    ' State level properties
    elif key$="active_player" : activePlayer = val(value$)   ' active_player
    elif key$="board" : board$ = value$   ' board
    elif key$="message" : message$ = value$
    endif
  endif

  ' Toggle if we are reading a key or a value
  isKey = not isKey
 loop

 ' A successful connection has been made. Reset error count.
 errorCount = 0 

ENDPROC


' ============================================================================
' Call the server api endpoint
PROC ApiCall apiPath

  ' Set up URL
  temp$ = "N:"
  temp$ =+ serverEndpoint$
  temp$ =+ $(apiPath)
  temp$ =+ query$
  temp$ =+ ""$9B

  PRINT temp$

  ' Open connection
  pause
  NOPEN 8, 12, 0, temp$

  ' If not successful, then exit.
  IF SErr()<>1
    @SetError &"COULD NOT CONNECT TO SERVER":EXIT
  ENDIF

  ' Change channel mode to JSON (1)
  pause
  SIO $71, 8, $FC, $00, 0, $1F, 0, 12, 1

  ' Ask FujiNet to parse JSON
  pause
  SIO $71, 8, $50, $00, 0, $1f, 0, 12, 0

  ' If successfully parsed JSON, update state
  IF SErr()=1
    @UpdateState
  ELSE
    @SetError &"COULD NOT PARSE JSON":EXIT
  ENDIF

  ' Close connection
  pause
  NCLOSE 8
ENDPROC

' ============================================================================
' Calls the server, picking the appropriate path
Proc CallServer
  if len(requestedMove$)>0
    path$ = "move/"
    path$ =+ requestedMove$
    requestedMove$=""
  else
    path$ = "state"
  endif

  ' Call the server (updates state on every response)
  @ApiCall &path$
endproc

Proc LeaveServer
  @ApiCall &"leave"
endproc

PROC PrintBoard
    PRINT board$[1, 15]
    PRINT board$[17, 15]
    PRINT board$[33, 15]
    PRINT board$[49, 15]
    PRINT board$[65, 15]
    PRINT board$[81, 15]
    PRINT board$[97, 15]
    PRINT board$[113, 15]
ENDPROC

' IMPORTANT in C if strlen(query) == 0) it will grab a table list and 
' force the player to choose a table.


' IMPORTANT in C the main loop 
'     // Main in-game loop
'    while (true) {
'
'        // Get latest state and draw on screen, then prompt player for move if their turn
'        if (getStateFromServer()) {
'            showGameScreen();
'            requestPlayerMove();
'        } else {
'            // Wait a bit to avoid hammering the server if getting bad responses
'            pause(30);
'        }
'
'        // Handle other key presses
'        readCommonInput();
'
'        switch(inputKey) {
'            case KEY_ESCAPE: // Esc
'            case KEY_ESCAPE_ALT: // Esc Alt
'                showInGameMenuScreen();
'                break;
'        }
'
'
'    }
do
    PRINT "-------"
    ' get state from server
    @CallServer   
    
    @PrintBoard
    print message$
    if errorCount = 0
        INPUT "Your move:";requestedMove$
        @CallServer   
    else
        pause 10
    endif

   
loop
