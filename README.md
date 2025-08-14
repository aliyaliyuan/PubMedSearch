## Welcome to PubMedSearch and PubMedSearch Slackbot!

This program integrates the PubMed, AirTable, and Slackbot APIs to create an automated custom query in PubMed that stores the articles and their metadata (i.e. author, title, link to read, etc.) in AirTable. Each time the table is updated, a message in slack will be sent updated the total number of articles and the last date of an update. 
I made this for the lab I worked at, since one of their projects required sifting through all articles that mention certain keywords and/or reference a specific article. The base in AirTable allows them to track all relevant articles, and to mark off ones they have already read and analyzed for their project. 

This can be customized for any specific query. 

## Before using this application, you must change API_KEY, BASE_ID, and TABLE_ID to your own personal access key, the base ID of interest, and the table ID of interest.

Below is a step-by-step tutorial on how to obtain your own personal access key 

1. Go to https://airtable.com/create/tokens
2. Select the blue "+ Create token" button to the right
![p1](https://github.com/user-attachments/assets/5f310f76-bbff-470d-b0b7-cd331f24fa2d)


3. Name your token

![p2](https://github.com/user-attachments/assets/faf5f3ab-748c-4a52-a380-4f289298c8da)


4. Click "Add Scope" and add as many permissions as possible

   ![p3](https://github.com/user-attachments/assets/a6c19043-34cf-464a-9dac-e46f6299d120)


6. Click "Add Base" and select the base you want this application to write/update to

![p4](https://github.com/user-attachments/assets/567fa137-fad8-43e3-bac5-193d815a3c36)

7. Copy the token and put it somewhere secure

8. Go into PubMedSearch.py in this repo and change API_KEY to your new token

9. Change BASE_ID and TABLE_ID to your base ID and table ID (it's in the url of the table when you are accessing it)
   I.E. In https://airtable.com/app123b/tbl3452/viwKSO "app123b" is the BASE_ID and "tbl435w" is the TABLE_ID

10. Now, you may run "python PubMedSearch.py"
    
11. It creates a log.txt file to keep the last date it was updated. This means the next time you run the code, it will search for articles AFTER the last time you updated.

## Slackbot integration

1. If you want to implement a Slackbot to send notifications to a channel that a more articles were pushed to AirTable from PubMed, obtain a Slack Webhook URL
   Instructions can be found at this link: https://api.slack.com/messaging/webhooks

2. Update "SLACK_WEBHOOK_URL"

3. Run "python PubMedSlackbot.py"

## Automation

I used Windows Task Scheduler to have this program run once a month on a Windows PC. I was making this for a lab that I worked at, but was leaving, so I needed it to be simple and easy to automate. That is why I had this create a csv that is saved to the Windows PC. This means if something broke regarding the AirTable API (i.e. unexpected changed permissions) , they would still have access to the table of relevant PubMed articles. rok

## Tips
I would keep these two python scripts in the same directory. 



   

