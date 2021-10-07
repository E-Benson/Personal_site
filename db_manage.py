import boto3
from boto3.dynamodb.conditions import Key, Attr
from creds import credentials
import configparser


class Database():
    
    def __init__(self):
        self.a_key = credentials["access_key"]
        self.s_key = credentials["secret_key"]
        self.region = "us-east-1"

    def a_key(self):
        return self.a_key

    def s_key(self):
        return self.s_key

    def region(self):
        return self.region
       

class Notifications_DB(Database):
    def __init__(self):
        super().__init__()
        self.stat_db = boto3.resource('dynamodb', 
                                region_name=super().region(),
                                aws_access_key_id=super().a_key(),
                                aws_secret_access_key=super().s_key()
                                )
        self.table = self.stat_db.Table("Ammo_Notifications")
        self.primary_key = self.table.key_schema[0]["AttributeName"]
        self.sort_key = self.table.key_schema[1]["AttributeName"]
        print(self.primary_key)
        #self.push_item("www.google.com", "terseesgd@appstate.edu")
        #items = self.get_item("www.google.com")
        x = self.get_item("https://www.wikiarms.com/go/6042008?origin=web")
        print(x)
        users = ["terseesgd@appstate.edu"]
        #self.delete_items("www.google.com", users)
        #self.delete_items("www.google.com")
        """
        res = self.get_item({"site_url": "www.google.com"})
        print(res)
        res["user_list"].append("tpppp@appstate.edu")
        print(res)
        self.update_item(res)
        """
        print(self.table.key_schema)
   
    def push_item(self, url, email):
        data = {"site_url": url, "email": email, "is_notified": True}
        self.table.put_item(Item=data)
        return True
        
        
    def delete_items(self, url, emails):
        key = {
                self.primary_key: url,
                self.sort_key: None
              }
        with self.table.batch_writer() as bat:
            for email in emails:
                key[self.sort_key] = email
                print(f"\tDeleting: {key}")
                bat.delete_item(Key=key)
        
   

    def get_item(self, url, email=None):
        #target_url = item["site_url"]
        if email is None:
            res = self.table.query(
                        KeyConditionExpression=
                            Key("site_url").eq(url)
                        )
        else:
            res = self.table.query(
                            KeyConditionExpression=
                                Key(self.primary_key).eq(url) & Key(self.sort_key).eq(email)
                            )
        if len(res["Items"]) < 1:
            return None
        if len(res["Items"]) == 1:
            return res["Items"][0]
        return res["Items"]

        
        
    def update_item(self, item):
        key = {
                self.primary_key: item[self.primary_key]
              }
        print(item)
        u_exp = "SET user_list = :val1"
        exp_list = []
        for user in item["user_list"]:
            exp_list.append(user)
        print(exp_list)
        exp_vals = {":val1": {"SS": item["user_list"]}}
        print(exp_vals)
        
        self.table.update_item(
                            Key=key,
                            UpdateExpression=u_exp,
                            ExpressionAttributeValues=exp_vals
                        )
        
        return True

    def add_user(self, email):
        pass


class Stat_DB(Database):

    def __init__(self):
        super().__init__()
        self.stat_db = boto3.resource('dynamodb', 
                                region_name=super().region(),
                                aws_access_key_id=super().a_key(),
                                aws_secret_access_key=super().s_key()
                                )
        self.table = self.stat_db.Table("Ammo_Statistics")

        print(self.stat_db.Table("Ammo_Statistics"))


    def push_item(self, item):
        self.table.put_item(Item=item)
        return True
       
    
    def query_items(self, cal, date=None):
        if date is None:
            res = self.table.query(
                    KeyConditionExpression=Key("caliber").eq(cal)
                    )
            if len(res["Items"]) < 1:
                return None
            return res["Items"]
        else:
            res = self.table.query(
                    KeyConditionExpression=
                        Key("caliber").eq(cal) & Key("date_str").eq(date)
                    )
            #print(res["Items"])
            if len(res["Items"]) == 1:
                return res["Items"][0]
            return None


    def test(self):
        x = [
                {"caliber": "22lr", "date_str": "January-10-2020", "min_price": "0.25", "max_price": "1.90"},
                {"caliber": "22lr", "date_str": "January-11-2020", "min_price": "0.53", "max_price": "1.21"},
                {"caliber": "22lr", "date_str": "January-12-2020", "min_price": "0.15", "max_price": "1.45"},
                {"caliber": "308", "date_str": "January-10-2020", "min_price": "0.65", "max_price": "2.45"}
            ]
        #print(self.push_item(x[0]))
        for i in x:
            self.push_item(i)
        print(self.query_items("22lr"))
        print(self.query_items("22lr", "January-10-2020"))

        
class Ammo_DB(Database):
    
    def __init__(self):
        super().__init__()
        self.primary_key = "site_url"
        self.sort_key = "cpr"
        self.db = boto3.resource('dynamodb', 
                            region_name=super().region(),
                            aws_access_key_id=super().a_key(),
                            aws_secret_access_key=super().s_key()
                            )
        self.table_prefix = "Ammo_Listings_{}"
        self.tables = dict()
        self.conf = configparser.ConfigParser()
        self.conf.read("conf.ini")
        for a_type in self.conf["AMMOTYPES"]:
            self.tables[a_type] = self.db.Table(self.table_prefix.format(a_type))
            
    
    def push_item(self, item):
        cal = item['caliber']
        self.tables[cal].put_item(Item=item)
        return True
        
        
    def push_many_items(self, items):
        cal = items[0]["caliber"]
        table = self.tables[cal]
        with table.batch_writer() as bat:
            for item in items:
                print(f"\tPushing: {item['site_url']}\t{item['cpr']}")
                res = bat.put_item(item)
                #print(res)
        return True
        
    
    def delete_item(self, item):
        cal = item["caliber"]
        table = self.tables[caliber]
        key = {
                self.primary_key: item[self.primary_key],
                self.sort_key: item[self.sort_key]
              }
        self.tables[cal].delete_item(Key=key)
    

    def delete_many_items(self, items):
        cal = items[0]["caliber"]
        table = self.tables[cal]
        with table.batch_writer() as bat:
            for item in items:
                key = { self.primary_key: item[self.primary_key],
                        self.sort_key: item[self.sort_key]
                        }
                print(f"\tDeleting: {item['site_url']}\t{item['cpr']}")
                bat.delete_item(Key=key)#{primary_key: item[primary_key], sort_key: item[sort_key]})
                #print(res)
        return True

    
    def update_item(self, item):
        table = self.tables[item["caliber"]]
        key = {
                self.primary_key: item[self.primary_key],
                self.sort_key: item[self.sort_key]
              }
        for k in item.keys():
            if k != self.primary_key and k != self.sort_key:
                u_exp = f"SET {k} = :val1"
                exp_vals = {":val1": item[k]}
                table.update_item(
                        Key=key,
                        UpdateExpression=u_exp,
                        ExpressionAttributeValues=exp_vals
                        )
        return True



    
    def query_items(self, cal, target=None):
        table = self.tables[cal]
        if target is None:
            res = table.query(
                    KeyConditionExpression=Key("caliber").eq(cal)
                    )
        else:
            try:
                res = table.query(
                    KeyConditionExpression=Key(self.primary_key).eq(target["site_url"])
                    )
                return res["Items"][0]
            except:
                return None
        #print(f"Res:\n{res}")
        return res['Items']
        
    
    # Will be removed and replaced with query_items
    def query_item(self, cal, target):
        table = self.tables[cal]
        res = table.query(
                KeyConditionExpression=Key(primary_key).eq(target)
                )
        return res['Items']
        
        
    def scan_items(self, cal):
        table = self.tables[cal]
        res = table.scan(
                FilterExpression=Attr('caliber').eq(cal)
                )
        return res["Items"]
        
        
    def empty_table(self, a_type):
        items = self.scan_items(a_type)
        self.delete_many_items(items)
        return True


    def test(self):
        a_list1 = {
                "site_url": "www.google.com",
                "cpr": "0.45",
                "price": "19.99",
                "caliber": "22lr",
                "stock": "in stock",
                "descr": "This is really good ammo I promise",
                "change": "25m ago"
                }
        a_list2 = a_list1.copy()
        a_list2["site_url"] = "www.youtube.com"
        a_list2["cpr"] = "0.34"
        a_list3 = a_list1.copy()
        a_list3["site_url"] = "www.reddit.com"
        a_list3["cpr"] = "0.01"
        a_list = [a_list1, a_list2, a_list3]
        _pass = True
        print("Testing Ammo_DB")
        try:
            self.push_item(a_list1)
            print(">>>\tAdd items to db")

        except:
            print("!--\tCannot add items")
        try:
            listing = self.query_items("22lr", a_list1)
            listings = self.scan_items("22lr")
            if listings is not None and len(listings) >= 1:
                print(">>>\tRetrieved items")
        except:
            _pass = False
            print("!--\tCannot retrieve items")
        try:
            res = self.push_many_items(a_list)
            for a in a_list:
                found = self.query_items(a["caliber"], target=a)
                if found["site_url"] != a["site_url"]:
                    raise Exception
            print(">>>\tPushed many items")
        except:
            _pass = False
            print("!--\tCannot add many items")
        try:
            res = self.scan_items("22lr")
            sites = [x["site_url"] for x in a_list]
            for item in res:
                if item["site_url"] in sites:
                    sites.remove(item["site_url"])
            if len(sites) >= 1:
                raise Exception
            print(">>>\tScan items")
        except:
            _pass = False
            print("!--\tCannot scan items")
        try:
            res = self.delete_many_items(a_list)
            if res is not True:
                raise Exception
            for a in a_list:
                if self.query_items(a["caliber"], a) is not None:
                    raise Exception
            print(">>>\tDelete many items")
        except:
            _pass = False
            print("!--\tCannot delete items")
        return _pass
    
    

class User_DB(Database):
    
    def __init__(self):
        super().__init__()
        self.db = boto3.resource("dynamodb",
                                region_name=super().region(),
                                aws_access_key_id=super().a_key(),
                                aws_secret_access_key=super().s_key()
                                )
        self.table = self.db.Table('UserList')
        self.conf = configparser.ConfigParser()
        self.conf.read("conf.ini")
        self.a_types = list()
        for a_type in self.conf["AMMOTYPES"]:
            self.a_types.append(a_type)
        
        
    def add_user(self, user_data):
        user_data["email"] = user_data["email"].lower()
        user_data["phone"] = ""
        user_data["notifications"] = False
        user_data["sms_count"] = "0"
        for a_type in self.a_types:
            user_data[a_type] = "0.0"
        self.table.put_item(
                Item=user_data
                )
        return True
        
        
    def inc_sms_count(self, email):
        user = self.get_user(email)
        sms_count = int(user["sms_count"])
        sms_count += 1
        self.update_user(email, {"sms_count": str(sms_count)})
        return True
    
        
        
    def update_user(self, email, data):
        key = {"email": email}
        update_data = dict()
        for k in data.keys():
            update_data[k] = {"Value": data[k], "Action": "PUT"}
        self.table.update_item(
                Key=key, 
                AttributeUpdates=update_data
                )
        return True
        
        
    def get_user(self, email):
        try:
            res = self.table.scan(
                    FilterExpression=Attr('email').eq(email.lower())
                    )
            return res["Items"][0]
        except:
            return ""
            
            
    def get_password(self, email):
        try:
            res = self.table.scan(
                    FilterExpression=Attr('email').eq(email.lower())
                    )["Items"]
            return res[0]["p_hash"]
        except:
            return None
        
        
    def get_users_to_notify(self):
        res = self.table.scan(
                FilterExpression=Attr('notifications').eq(True)
                )["Items"]
        #for user in res:
            #print(f"User list: {user}")
        return res
        
       

    def test(self):
        u_email = "test@testing.com"
        u_pass = "123123123"
        u_phone = "9196623728"
        u_notifications = True
        u_22lr = "0.12"
        u_223 = "0.36"
        u_308 = "0.76"
        u_data = {
            "email": u_email,
            "p_hash": u_pass
            }
        u_settings = {
            "phone": u_phone,
            "notifications": u_notifications,
            "22lr": u_22lr,
            "223": u_223,
            "308": u_308
            }
        self.update_user(u_data["email"], {"22lr": "0.24"})
        _pass = True
        print("Testing User_DB")
        try:
            schema = self.table.key_schema[0]
            print(">>>\tConnected to db")
        except Exception as e:
            _pass = False
            print(f"!--\tCannot connect to db")
        try: 
            self.add_user(u_data)
            print(">>>\tAdd users")
        except:
            _pass = False
            print("!--\tCannot add users")
        try:
            user = self.get_user(u_data["email"])
            if user["p_hash"] != u_data["p_hash"]:
                raise Exception
            print(">>>\tPull user data")
        except:
            _pass = False
            print("!--\tCannot get user data")
        try:

            self.update_user(u_data["email"], u_settings)
            user = self.get_user(u_data["email"])
            if user["22lr"] != u_settings["22lr"]:
                raise Exception
            print(">>>\tUpdated user")
        except:
            _pass = False
            print("!--\tCannot update users")
        try:
            users = self.get_users_to_notify()
            for u in users:
                if u["email"] == u_data["email"]:
                    print(">>>\tGet users to notify")
        except:
            _pass = False
            print("!--\tCannot get notifications")
        return _pass




if __name__ == "__main__":
    user_db = User_DB()
    ammo_db = Ammo_DB()
    stat_db = Stat_DB()
    notify_db = Notifications_DB()
    #notify_db.
    #stat_db.test()
    #user_db.test()
    #ammo_db.test()
    #ammo_db.test_scrape()
    #user_db.inc_sms_count("eabenson95@gmail.com")
    test_item = {"site_url": "www.google.com", "cpr": "0.11", "stock": "In stock", "caliber": "22lr"}
    #print(ammo_db.scan_items("22lr"))
    #ammo_db.empty_table("22lr")
    #res = ammo_db.get_item(test_item)
#    test_item["stock"] = "Backorder"
    #ammo_db.update_item(test_item)
    #res = ammo_db.query_items(test_item["caliber"], test_item)
    #print(res)
    """
    test_item = {"site_url": "www.google.com", "cpr": "0.11", "status": "In stock", "caliber": "22lr"}
    ammo_db.push_item(test_item)
    res1 = ammo_db.query_items(test_item["caliber"], test_item)
    test_item["status"] = "Backorder"
    ammo_db.update_item(test_item)
    res2 = ammo_db.query_items(test_item["caliber"], test_item)
    print(res1)
    print(res2)
    """   
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
