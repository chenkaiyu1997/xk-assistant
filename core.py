# -*- coding: UTF-8 -*-
import requests,time,json,os,re
import logging
from captcha_solver import CaptchaSolver
from io import StringIO
from  multiprocessing.dummy import Pool as ThreadPool
from datetime import datetime
from datetime import timedelta


basedir = os.path.abspath(os.path.dirname(__file__))
formdata={
    "username":"x",
    "password":"x"
}
loginheaders={
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
}
postheaders={
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    "Content-Type":"application/x-www-form-urlencoded"
}
classtomonitor=["ECON119002.01"]
classtorush2=["ECON119002.01","PEDU110076.06","PEDU110102.14","COMP130002.01","COMP130003.01","COMP130004.01","COMP130149.01","COMP130150.01"]
classtorush=["ENGL110064.04","ENGL110061.19","ENGL110066.02"]
hascaptcha=False
coo=None

def login():
    global coo

    loginresult=requests.get("http://xk.fudan.edu.cn/xk/login.action",headers=loginheaders)
    coo=loginresult.cookies

    if "captcha" in loginresult.text:
        postheaders["captcha_response"] = solve_captcha()

    time.sleep(1)
    postresult=requests.post("http://xk.fudan.edu.cn/xk/login.action",cookies=coo,data=formdata,headers=postheaders)
    if "Ldap" in postresult.text:
        logging.debug("Password Error!")
    if "editAccount" in postresult.text:
        print("Login success!")
        with open(os.path.join(basedir,"tmpcookie.coo"),"w") as f:
            json.dump(requests.utils.dict_from_cookiejar(coo),f)
        return True
    else:
        return False

def checklogin():
    global coo
    check=requests.get("http://xk.fudan.edu.cn/xk/home.action",cookies=coo,headers=loginheaders)
    if not "editAccount" in check.text:
        return False
    return True

def getclassdata():

    global coo
    getclassheaders={
        "If-None-Match": "1467507601847_326716",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "xk.fudan.edu.cn",
    }

    defaultpage=requests.get("http://xk.fudan.edu.cn/xk/stdElectCourse!defaultPage.action?electionProfile.id=403",cookies=coo,headers=getclassheaders)

    if "document.loginForm" in defaultpage.text:
        return False
    mystr=defaultpage.text[-300:]
    mystr = mystr.replace("\n", "")
    mystr = mystr.replace("\r", "")
    mystr = mystr.replace("\t", "")

    global hascaptcha
    hascaptcha= (re.match(r'.*(\w+)e,0,0];.*',mystr).groups()[0])=='u'

    if False :
        recclassdata=requests.get("http://xk.fudan.edu.cn/xk/stdElectCourse!data.action?profileId=403",cookies=coo,headers=getclassheaders)
        if recclassdata.status_code == 304:
            logging.debug("class data not modified")
        elif recclassdata.status_code== 500:
            logging.error("server error!")
            print(recclassdata.request.headers)
            print(recclassdata.request.url)
        else:
            logging.debug("class data modified")
            with open(os.path.join(basedir,"classdata.raw"),"w") as f:
                f.write(recclassdata.text)
            os.system(os.path.join(basedir,"classdata_processor"))
            time.sleep(0.1)

    with open(os.path.join(basedir,"classdata.json"), "r") as f:
        classdata=json.load(f)

    global classtomonitor
    global classtorush
    i=0
    try:
        for i in range(len(classtomonitor)):
            classtomonitor[i]=classdata[classtomonitor[i]]
    except BaseException:
        print("there may not beclass %s" % classtomonitor[i])

    i = 0
    try:
        for i in range(len(classtorush)):
            classtorush[i] = classdata[classtorush[i]]
    except BaseException:
        print("there may not beclass %s" % classtorush[i])
        return False

    logging.debug(classtorush)
    return True

def prepareprocess(waittime=1):
    global coo
    with open(os.path.join(basedir,"tmpcookie.coo"),"r") as f:
        try:
            coo = requests.utils.cookiejar_from_dict(json.load(f))
            logging.debug(coo)
        except json.JSONDecodeError:
            logging.debug("Json error")
            coo=None

    # while (not checklogin()) or (not getclassdata()):
    while not checklogin():
        print("login!")
        while not login():
            time.sleep(1)
        time.sleep(waittime)
    else:
        print("Already logged in")

    getclassdata()

def check(fre=5):
    global coo
    prepareprocess()
    for i in range(1000000000):

        nowdataraw = requests.get("http://xk.fudan.edu.cn/xk/stdElectCourse!queryStdCount.action?projectId=1&semesterId=242&_=" + time.time(),cookies=coo, headers=loginheaders)
        if "document.loginForm" in nowdataraw.text:
            time.sleep(60)
            prepareprocess()

        print(nowdataraw.text)
        nowdata = nowdataraw.content.decode('utf-8').split("\n")[1]
        global classtomonitor
        for j in classtomonitor:
            subans = re.match(r".*"+j+"':{sc:(\d+),lc:(\d+).*",nowdata).groups()
            if subans :
                if subans[0] != subans[1] :
                    print("You can select %s!" % j)
                    rush(j)
                else:
                    print("%s is full" % j)

        # nowdata = json.loads(str)
        # logging.debug(nowdata['592003'])
        time.sleep(fre)

def solve_captcha():
    solver =CaptchaSolver('browser')
    imgdata = requests.get("http://xk.fudan.edu.cn/xk/captcha/image.action?d=" + time.time(), cookies=coo,headers=loginheaders)
    print(imgdata.headers)
    ans=solver.solve_captcha(imgdata.content)
    return ans


def rush(coursecode):
    global coo
    global hascaptcha
    print("Applying %s" % coursecode)

    rushdata = {
        "optype": "true",
        "operator0": str(coursecode) + ":true:0"
    }

    if hascaptcha:
        rushdata["captcha_response"] = solve_captcha()

    postresult=requests.post("http://xk.fudan.edu.cn/xk/stdElectCourse!batchOperator.action?profileId=403",cookies=coo,data=rushdata,headers=postheaders)
    if "与以下课程冲突" in postresult.text:
        print("Time Conflict")
    elif "公选人数已满" in postresult.text:
        print("No quota")
    elif "document.loginForm" in postresult.text:
        prepareprocess()
    elif "成功" in postresult.text:
        print("Success!")
    elif "你已经选过" in postresult.text:
        print("Already Success!")
    elif "操作失败,请联系管理员" in postresult.text:
        print("Seems to be successful")
    elif "过快点击" in postresult.text:
        print("Click too fast")
    elif "内部错误" in postresult.text:
        print("Server internal error")
    else:
        print("Unknown situation")
        print(postresult.text)


def core():
    logging.basicConfig(level=logging.WARNING)
    # check()
    prepareprocess()

    pool=ThreadPool(20)
    time1 = datetime.now()
    timeend= time1+timedelta(minutes=2)

    while True:
        time2 = datetime.now()
        if(time2>timeend):
            break
        for i in classtorush:
            pool.apply_async(rush,args=(i,))
            time.sleep(0.25)
    time.sleep(10)
    pool.terminate()
    pool.join()
