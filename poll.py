"""Public FEMI Telegram gateway: only owner-authorized updates go to private worker."""
import base64
import json
import os
import requests
from datetime import datetime, timedelta, timezone

API="https://api.github.com"
REPO=os.getenv("GITHUB_REPOSITORY","Ajibola19/Femi-Public-Controller")
PRIVATE="Ajibola19/Femi-GitHub-Actions"
SESSION=requests.Session()
TOKEN=os.environ["TELEGRAM_BOT_TOKEN"]
OWNER=str(os.environ["TELEGRAM_CHAT_ID"])
DISPATCH_TOKEN=os.environ["PRIVATE_REPO_DISPATCH_TOKEN"]
GH_TOKEN=os.environ["GITHUB_TOKEN"]
STATE_PATH="state/offset.json"
WAT=timezone(timedelta(hours=1))

def github(method,url,*,token,**kwargs):
    headers={"Authorization":f"Bearer {token}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    response=SESSION.request(method,url,headers=headers,timeout=25,**kwargs)
    response.raise_for_status()
    return response

def load_state():
    url=f"{API}/repos/{REPO}/contents/{STATE_PATH}"
    r=SESSION.get(url,headers={"Authorization":f"Bearer {GH_TOKEN}","Accept":"application/vnd.github+json"},timeout=20)
    if r.status_code==404:
        return {"offset":0,"last_short_slot":"","last_long_check":""},None
    r.raise_for_status()
    blob=r.json()
    return json.loads(base64.b64decode(blob["content"])),blob["sha"]

def save_state(state,sha):
    data=base64.b64encode((json.dumps(state,sort_keys=True)+"\n").encode()).decode()
    payload={"message":"Advance public FEMI polling cursor","content":data,"branch":"main"}
    if sha: payload["sha"]=sha
    response=github("PUT",f"{API}/repos/{REPO}/contents/{STATE_PATH}",token=GH_TOKEN,json=payload)
    return response.json()["content"]["sha"]

def dispatch(kind,payload):
    r=github("POST",f"{API}/repos/{PRIVATE}/dispatches",token=DISPATCH_TOKEN,
             json={"event_type":kind,"client_payload":payload})
    if r.status_code!=204:
        raise RuntimeError(f"Unexpected private dispatch response: {r.status_code}")

def fetch_updates(offset):
    r=SESSION.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                  params={"offset":offset,"timeout":0,"limit":100,
                          "allowed_updates":json.dumps(["message","edited_message"])},timeout=25)
    r.raise_for_status()
    value=r.json()
    if not value.get("ok"):raise RuntimeError("Telegram getUpdates returned error")
    return value.get("result",[])

def main():
    state,sha=load_state()
    offset=int(state.get("offset",0))
    webhook=SESSION.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook",json={"drop_pending_updates":False},timeout=20)
    webhook.raise_for_status()
    if not webhook.json().get("ok"):
        raise RuntimeError("Failed to disable Telegram webhook without dropping pending updates")
    updates=fetch_updates(offset)
    for update in updates:
        uid=int(update["update_id"])
        message=update.get("message") or update.get("edited_message") or {}
        sender=str(message.get("chat",{}).get("id",""))
        if sender==OWNER:
            # Private worker has no access to public-repository secrets.
            dispatch("femi-telegram-update",{"telegram_update":update})
        state["offset"]=uid+1
        sha=save_state(state,sha)
        print("Telegram update forwarded or ignored safely; offset advanced",flush=True)
    now=datetime.now(WAT)
    for index,hour in ((1,8),(2,15),(3,20)):
        minutes=(now.hour-hour)*60+now.minute
        key=f"{now:%Y%m%d}-slot-{index}"
        if 0<=minutes<20 and state.get("last_short_slot")!=key:
            dispatch("femi-slot-heartbeat",{"slot_key":key})
            state["last_short_slot"]=key
            sha=save_state(state,sha)
            print(f"Short prompt heartbeat: {key}",flush=True)
    # GitHub scheduled workflows are best-effort. Send one backup wake-up
    # during each visual window; the private worker's MySQL window claim
    # prevents reprocessing if the normal visual schedule already ran.
    for visual_window,hour,minute in (("morning",6,25),("night",22,25)):
        minutes_now=now.hour*60+now.minute
        start=hour*60+minute
        visual_key=f"{now:%Y%m%d}-{visual_window}"
        state_key=f"last_visual_backup_{visual_window}"
        if start<=minutes_now<start+25 and state.get(state_key)!=visual_key:
            dispatch("femi-visual-backup",{"window":visual_window,"day":f"{now:%Y%m%d}"})
            state[state_key]=visual_key
            sha=save_state(state,sha)
            print(f"Backup visual wakeup forwarded: {visual_key}",flush=True)
    # Long dispatcher checks four times daily; long visual prep has its own schedule.
    window=f"{now:%Y%m%d}-{now.hour//6}"
    if state.get("last_long_check")!=window:
        dispatch("femi-long-heartbeat",{"window":window})
        state["last_long_check"]=window
        save_state(state,sha)
        print("Long-form dispatch check forwarded",flush=True)

if __name__=="__main__":
    main()
