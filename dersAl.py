from asyncio import constants
import requests
from lxml import html
import getpass
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import yagmail

xpathStringDersAl = "//td[contains(@class,'dddefault')]"
xpathStringDersEkle = "//table[contains(@summary,'Error')]"
xpathStringInfoText = "//span[contains(@class,'infotext')]/text()"
s = requests.session()
sifre = ""
kullanıcıAdı = ""
password = "bisiler"




data = {

                "term_in": "",
        "RSTS_IN":["DUMMY","RW","RW","RW","RW","RW","RW","RW","RW","RW","RW"],
        "assoc_term_in":["DUMMY","","","","","","","","","",""],
        "CRN_IN":["DUMMY","","","","","","","","","",""],
        "start_date_in":["DUMMY","","","","","","","","","",""],
        "end_date_in":["DUMMY","","","","","","","","","",""],
        "SUBJ":["DUMMY"],
        "CRSE":["DUMMY"],
        "SEC":["DUMMY"],
        "LEVL":["DUMMY"],
        "CRED":["DUMMY"],
        "GMOD":["DUMMY"],
        "TITLE":["DUMMY"],
        "MESG":["DUMMY"],
        "REG_BTN":["DUMMY","Submit+Changes"],
        "regs_row":"0",
        "wait_row":"0",
        "add_row":"10",
        }


def mailAt(email,topic,description):
    user = 'kayitbotsu@gmail.com'
    app_password = password  # a token for gmail
    to = email

    subject = topic
    content = [description]
    try:
        with yagmail.SMTP(user, app_password) as yag:
            yag.send(to, subject, content)
            print('Mail başarıyla gönderildi')
    except:
        print("Mail sorun çıktıgından dolayı gönderilemedi")



def dersCrnListesiAl(_donem):
    data["term_in"] = _donem
    eklenilcekDerslerCrn = []
    while(True):
        dersCrnları = input("Ekleyeceginiz ders crnını yazıp entera basın bağlı ders girecekseniz araya virgul koyun  (q ile ders eklemeyi bitirebilirsiniz): ")
        if(dersCrnları == "q"):
            return eklenilcekDerslerCrn
        eklenilcekDerslerCrn.append(dersCrnları.split(","))

def bosDersListesiDon(eklenilcekDerslerCrn,donem):
    threads= []
    bosDersListesi = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        for bagliDersler in eklenilcekDerslerCrn:
            threads.append(executor.submit(bagliDerslerBosmu,bagliDersler,donem))
        for task in as_completed(threads):
            result = task.result()
            if(result[0]):
                print("{} dersi boş".format(result[1]))
                bosDersListesi.extend(result[1])

    return bosDersListesi


def bagliDerslerBosmu(bagliDersler,donem):
    for dersCrn in bagliDersler:
        if(not dersBosmu(donem,dersCrn)):
            return [False,bagliDersler]
    return [True,bagliDersler]

def dersBosmu(donem,dersCrn):
    dersAramaUrl = "https://suis.sabanciuniv.edu/prod/bwckschd.p_disp_detail_sched?term_in={}&crn_in={}".format(donem,dersCrn)
    try:
        dersSayfasi =  requests.get(dersAramaUrl)
        if dersSayfasi.status_code == 200:
            tree = html.fromstring(dersSayfasi.text)
            path = tree.xpath(xpathStringDersAl)
            if len(path) > 0:
                kalanKontejyan = (int)(path[3].text)
                return kalanKontejyan > 0
        return False
    except requests.ConnectionError:
        return False


def girisYap():
    global sifre
    global kullanıcıAdı

    if(len(kullanıcıAdı) == 0):
        kullanıcıAdı = input("Kullanıcı Adınızı girin: ")
        sifre = getpass.getpass("Sifrenizi girin: ")

    try:
        s.get("https://suis.sabanciuniv.edu/prod/twbkwbis.P_SabanciLogin")
        page = s.get("https://suis.sabanciuniv.edu/prod/twbkwbis.P_ValLogin?sid={}&PIN={}".format(kullanıcıAdı,sifre))
        return page.url
    except requests.ConnectionError:
        print("Baglanti hatası")




def dersKaldir(eklenilcekDerslerCrn,crn):
    for bagliDersler in eklenilcekDerslerCrn:
        if crn in bagliDersler:
            eklenilcekDerslerCrn.remove(bagliDersler)




def Kaydol(donem,eklenilcekDerslerCrn):

    url = girisYap()
    print(url)

    tamEmail = kullanıcıAdı + "@sabanciuniv.edu"

    while(len(eklenilcekDerslerCrn) > 0):
        bosDersler = bosDersListesiDon(eklenilcekDerslerCrn,donem)
        print(bosDersler)
        if(len(bosDersler) > 0):
            index = 1
            for bosDers in bosDersler:
                data["CRN_IN"].insert(index,bosDers)
                index += 1




            while(True):
                try:
                    girisYap()
                    dersEkleSayfa = s.post('https://suis.sabanciuniv.edu/prod/su_registration.p_su_register', data=data)
                    if(dersEkleSayfa.url == "https://suis.sabanciuniv.edu/prod/su_registration.p_su_register"):
                        break
                except requests.ConnectionError:
                    print("Daha fazla baglanti hatasi")
                finally:
                    time.sleep(30)


            data["CRN_IN"] = ["DUMMY","","","","","","","","","",""]


            #todo  Dogru sitedemisni kontrol et bakım/ kapalı vb



            tree = html.fromstring(dersEkleSayfa.text)
            infoPath = tree.xpath(xpathStringInfoText)
            errorPath = tree.xpath(xpathStringDersEkle)


   


            if (infoPath and "Term not available" in  infoPath[0]):
                time.sleep(30)
                continue

            if(errorPath):
                errorInfos = errorPath[0]

                butunHatalar = ""

                for errorInfo in errorInfos[1:]:
                    subject = errorInfo[2].text
                    crn = errorInfo[1].text
                    errorMessage = errorInfo[0].text

                    if(not ("Closed Section" in  errorMessage or "Corequisite" in errorMessage)):
                        hataMesaj = "{} / {} Error: {} ders eklenemiyecek".format(subject,crn,errorMessage)
                        butunHatalar += hataMesaj + "\n"
                        print(hataMesaj)
                        dersKaldir(eklenilcekDerslerCrn,crn)

                    bosDersler.remove(crn)
                
                if butunHatalar:
                    try:
                        mailAt(tamEmail,"Bazı dersler eklenirken hata olustu",butunHatalar)
                    except:
                        pass


            #Eklenmis dersleri printle

            butunEklenenler = ""
            for ders in bosDersler:
                dersEkleMesaj = "{} CRN li ders eklendi".format(ders)
                print(dersEkleMesaj)
                butunEklenenler += dersEkleMesaj + "\n"
                dersKaldir(eklenilcekDerslerCrn,ders)
            if(butunEklenenler):

                try:
                    mailAt(tamEmail,"Bazı dersler başarıyla eklendi",butunEklenenler)
                except:
                    pass

            #Eklenmis dersleri Eklenilcek dersler listesinden cıkar

            eklenilcekDerslerCrn = [ders for ders in eklenilcekDerslerCrn if ders not in bosDersler]


