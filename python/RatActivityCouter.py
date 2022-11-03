import time

class RatActivityCounter():
    def __init__(self, ratid, ratio, rat_label = "unknown"):
        self.ratid = ratid
        self.active_licks = 0
        self.inactive_licks = 0
        self.rewards = 0
        self.touch_counter = 0
        self.syringe_empty = 0
        self.next_ratio = ratio
        self.rat_label = rat_label
        self.last_act_licks = {"time":float(time.time()), "scantime":0}
        self.last_inact_licks = {"time":float(time.time()), "scantime":0}
        self.pumptimedout = False

    # @staticmethod 
    def update_last_licks(self, lick_time, scan_time, act):
        if act:
            self.last_act_licks["time"] = lick_time
            self.last_act_licks["scantime"] = scan_time
        else:
            self.last_inact_licks["time"] = lick_time
            self.last_inact_licks["scantime"] = scan_time
    
    @staticmethod
    def colored_print(ratID, act_count, inact_count, reward_count, timeout):
        print (ratID+ \
            "\x1b[0;32;40m" + \
            ": Active=" + str(act_count)+ \
            "\x1b[0m" + \
            "\x1b[0;33;40m" + \
            " Inactive="+str(inact_count) + \
            "\x1b[0m" + \
            "\x1b[0;32;40m" + \
            " Reward=" +  str(reward_count) + \
            "\x1b[0m" + \
            "\x1b[0;35;40m" + \
            " Timeout: "+ str(timeout) + \
            "\x1b[0m"
            )

    @staticmethod
    def show_data(devID, sesID,sessionLength, schedule, lapsed,
                  rat1,rat2,rat_unknown, phase="progress"):
        if schedule == "pr":
            #minsLeft = int((sessionLength - (time.time() - rat1.last_act_licks["time"])) / 60)
            minsLeft1 = int((sessionLength - (time.time() - rat1.last_act_licks["time"])) / 60)
            minsLeft2 = int((sessionLength - (time.time() - rat2.last_act_licks["time"])) / 60)
            minsLeft3 = int((sessionLength - (time.time() - rat_unknown.last_act_licks["time"])) / 60)
            minsLeft = max (minsLeft1,minsLeft2,minsLeft3)
        else:
            minsLeft = int((sessionLength-lapsed)/60)
        if phase == "final":
            print("{} Session_{}".format(devID, sesID))

        print ("\x1b[0;31;40m" + \
                "[" + str(minsLeft) + " min Left]" + \
                "\x1b[0m")

        for rat in [rat1,rat2,rat_unknown]:
            RatActivityCounter.colored_print(rat.ratid, rat.active_licks,
                                             rat.inactive_licks, rat.rewards,
                                             rat.pumptimedout)
        return time.time() 
    
    def increase_syringe_empty(self):
        self.syringe_empty += 1

    def incr_rewards(self):
        self.rewards += 1

    def incr_active_licks(self):
        self.active_licks += 1

    def incr_inactive_licks(self):
        self.inactive_licks +=  1

    def incr_touch_counter(self):
        self. touch_counter += 1 

    def reset_touch_counter(self):
        self.touch_counter = 0
