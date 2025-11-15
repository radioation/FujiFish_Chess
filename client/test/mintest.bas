'' minimal example
''
'' @author Greg Gallard,  Borrows heavily from Eric Carr's 5card.bas
'' @email greggallardo at gmail dot com
'' @license gpl v. 3
'


' FujiNet AppKey settings. These should not be changed
AK_LOBBY_CREATOR_ID = 1     ' FUJINET Lobby
AK_LOBBY_APP_ID  = 1        ' Lobby Enabled Game
AK_LOBBY_KEY_USERNAME = 0   ' Lobby Username key
AK_LOBBY_KEY_SERVER = 6     ' 5 Card Stud Client registered as Lobby appkey 1

' my AppKey
AK_CREATOR_ID = $5364       ' creator id
AK_APP_ID = 1               ' minimal 
AK_KEY_SHOWHELP = 0         ' Shown help

DATA NAppKeyBlock()=0,0,0

' Read server endpoint stored from Lobby
serverEndpoint$="NA"
query$="NA"

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
dim player_name$(7)
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



' read players name from app key
' IMPORTANT  in C common  welcomActionVerifyPlayerName() calls
'read_appkey(AK_LOBBY_CREATOR_ID, AK_LOBBY_APP_ID, AK_LOBBY_KEY_USERNAME, tempBuffer);
@NReadAppKey AK_LOBBY_CREATOR_ID, AK_LOBBY_APP_ID, AK_LOBBY_KEY_USERNAME, &myName$
? myName$


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
    ' get state from server
   
    ' wait a bit if we must 

    ' check for esc to exit
   
loop
