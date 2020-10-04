#Our graphic so we can get the key as maybe live on Overlay or Output
$WhichTitle = "TickerHD3"

#the .xml gets appended
$SettingsName = "CricHQSettings2"

#Variables that should not change
#CricHQ public API location
$CricHQ = "https://www.crichq.com/api/v2/public`/"
#vMix API
$vMix = "http://127.0.0.1:8088/api"

function vMixUpdate {
    Param($field,$value)

    #******************************************************
    #Put in an error trap for if the field does not exist!!

    if ((Invoke-WebRequest ("$vMix/?Function=SetText&Input=$key&SelectedName=$field&Value=$value")).statuscode -eq 200) {}

}

#Get vMix data - see what input key WhichTitle is and get MatchID and apiKey
#This now gives us all the settings we need to go get the data from CricHQ
$resource = (($vMix)+'?')
$vMixXML = Invoke-RestMethod -Method Get -Uri $resource
$Settings = ($vMixXML.vmix.inputs.input | Where-Object {$_.title -eq (($SettingsName)+'.xaml')}).text
$matchID = ($Settings | Where-Object {$_.name -eq 'MatchID'})."#text"
$apiKey = ($Settings | Where-Object {$_.name -eq 'apiKey'})."#text"
$key = ($vMixXML.vmix.inputs.input | Where-Object {$_.title -eq (($WhichTitle)+'.xaml')}).key

#Collected data:
Write-Host "MatchID: $matchID apiKey: $apiKey vMix input key: $key"


$ActiveTitle = ($vMixXML.vmix.inputs.input | Where-Object {$_.number -eq $vMixXML.vmix.active}).Title
foreach ($overlay in $vMixXML.vmix.overlays.overlay) {
        if (Get-Member -inputobject $overlay -name '#text' -Membertype Properties) {
            $Title = ($vMixXML.vmix.inputs.input | Where-Object {$_.number -eq $overlay.'#Text'}).Title
            write-host $Title
            write-host $ActiveTitle
            if ($Title -eq "$WhichTitle.xaml") {
                Write-host "Overlay active"
                $ActiveTitle = "TickerHD3.xaml"
                }
            } 
        }

if ($ActiveTitle -eq "$WhichTitle.xaml") {
    Write-Host "Title $ActiveTitle is active - process..."

    $resource = (($CricHQ)+"matches/"+($MatchID)+"/live?api_token="+($apiKey))
    #$resource
    $MatchID_Live = Invoke-RestMethod -Method Get -Uri $resource 
    $ticker = "$($MatchID_Live.innings.battingTeam[0]) vs $($MatchID_Live.innings.bowlingTeam[0]) in $($MatchID_Live.matchType)        $($MatchID_Live.currentPartnership.nameString) $($MatchID_Live.currentPartnership.runs) off $($MatchID_Live.currentPartnership.balls) balls"

    write-host $ticker
    vMixUpdate -field AnimatedTicker -value $ticker
    
    }
#End

