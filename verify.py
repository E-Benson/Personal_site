import configparser
from db_manage import User_DB
class Verify():

    def __init__(self):
        self.password_data = dict()
        self.user_db = User_DB()
        self.conf = configparser.ConfigParser()
        self.conf.read("conf.ini")
        for key in self.conf["VERIFY_PASSWORD"].keys():
            self.password_data[key] = int(self.conf["VERIFY_PASSWORD"][key])
        print(self.password_data)
        

    def verify_password(self, password):
        msg = None
        nums = sum( [c.isdigit() for c in password] )
        alphas = sum ( [c.isalpha() for c in password] )
        ban_list = ["\"", "\'", "`", "\\"]
        bans = sum( [c in ban_list for c in password] )
        length = len(password)
        if nums < self.password_data["min_nums"]:
            msg = "Password does not contain enough numbers"
            return (msg, False)
        if alphas < self.password_data["min_alpha"]:
            msg = "Password does not contain enough letters"
            return (msg, False)
        if bans >= 1:
            msg = "Password contains invalid characters"
            return (msg, False)
        if length > self.password_data["max_length"]:
            msg = "Password is too long"
            return (msg, False)
        if length < self.password_data["min_length"]:
            msg = "Password is too short"
            return (msg, False)
        return (msg, True)

    
    def verify_email(self, email):
        msg = None
        if len(email) < 7:
            msg = "Email is too short"
            return (msg, False)
        if len(email) > 32:
            msg = "Email is too long"
            return (msg, False)
        if self.user_db.get_user(email) != "":
            msg = "User with that email already exists"
            return (msg, False)
        if "@" not in email:
            msg = "Invalid email"
            return (msg, False)
        if ".com" not in email[-5:] and ".edu" not in email[-5:]:
            msg = "Invalid email domain"
            return (msg, False)
        if any( [c.isspace() for c in email] ):
            msg = "Email cannot contain spaces"
            return (msg, False)
        return (msg, True)

    
    def verify_phone(self, phone):
        msg = None
        if any( [c.isalpha() for c in phone] ):
            msg = "Invalid characters in phone number"
            return (msg, False)
        if len(phone) < 10:
            msg = "Phone number is too short. Include area code"
            return (msg, False)
        if len(phone) > 10:
            msg = "Phone number is too long"
            return (msg, False)
        return (msg, True)
        
    
    def verify_cpr(self, cpr):
        msg = None
        # If there is a decimal and there are less the 2 decimal place
        if cpr.find('.') >= 0:
            if len(cpr[cpr.index('.'):]) >= 4:
                msg = "Only specify 2 or fewer decimal places. ($1.23)"
                return (msg, False)
        if any( [c.isalpha() for c in cpr] ):
            msg = "Do not include any letters in your phone number"
            return (msg, False)
        return (msg, True)
            
            


    def test(self):
        valid_password = ["abc123!@#", "PaSsW0rD_~+!", "|><,12 .1,2n1m9@GH$"]
        invalid_password = ["abcdhfihe", "123456789", "abc123\\xyz", "pass`word"," flj32\"#%@", "123", "101010101010101010101010101010101"]
        valid_email = ["x@y.com", "xyt@m.edu"]
        invalid_email = ["ayx @x.com", "aaa@ha.ru", "@.com" "12345678", "thisisonehellofanemail@forsomeonelikeyourself.com"]
        _pass = True
        print("Testing Verify")
        if not all( [self.verify_password(p) for p in valid_password] ):
            print("!--\tCannot verify valid passwords")
            _pass = False
        if any( [self.verify_password(p) for p in invalid_password] ):
            print("!--\tCannot reject invalid passwords")
            _pass = False
        if _pass:
            print(">>>\tVerify passwords")

        if not all( [self.verify_email(e) for e in valid_email] ):
            print("!--\tCannot verify valid emails")
            _pass = False
        if any( [self.verify_email(e) for e in invalid_email] ):
            print("!--\tCannot reject invalid emails")
            _pass = False
        if _pass:
            print(">>>\tVerify emails")
        return _pass

if __name__ == "__main__":
    v = Verify()
    print(v.test())
