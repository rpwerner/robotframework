import os
import sys


class TestRunnerExtension():

    global activedLicense
    global deactivedLicense
    global soiVersion

    """
        Initializes licenses by reading the license file given as input.
    """
    def initLicenses(self,licenseFileFullPathName=None):
        if licenseFileFullPathName is not None:
            self.activedLicense = []
            self.deactivedLicense = []
            self.get_active_license_from_server(str(licenseFileFullPathName))
            print "active licences from server"
            print self.activedLicense
            
    def initSoiVersion(self, soiVersion=None):
        self.soiVersion = soiVersion
            
    def getSoiVersion(self):
        return self.soiVersion
    """
        Called at every start of a test case. The tags of a test case are checked if they include license
        tags. If so the license tags should be contained in the license file otherwise the test case is skipped.
        Note that the skip is just a message but the test case will be marked as passed.
        
    """
    def shouldTestBeExecuted(self, name, tags):
        onLic = []
        offLic = [] 
        onLic,offLic = self.load_tags_into_list(tags,onLic,offLic)
        if not ((self.contain_sublist(self.activedLicense,onLic) or len(onLic) == 0) and (not(self.areOffLicsAvailable(self.activedLicense,offLic)) or len(offLic) == 0)):
            return False
        else: 
            return True

    def load_tags_into_list(self,tags,onLic,offLic):
        """
            Load the license tags(starts with licenseON or licenseOFF) from the test and load into two arrays.
            The required activated licenses should be taged with licenseON=lic2,lic2
            for the required deactivaed licenses should be tage with licenseOFF=lic2,lic2
        """
        for tag in tags:
            if tag.startswith('license'):
                # get the comma separated licenses string and convert into list 
                licenses = tag.split("=")[1].split(",")
                if tag.startswith('licenseON='):
                    onLic = self.merge_lists(onLic,licenses) 
                if tag.startswith('licenseOFF='):
                    offLic = self.merge_lists(offLic,licenses) 
        return (onLic,offLic)
   
    def areOffLicsAvailable(self, list, sublist):
        """
        Check whether the list contains sublist
        """
        counter = 0
        for index in range(0,len(sublist)):
            if (str(sublist[index]) in list):
                counter +=1
        if (str(counter) == "0"):
            return False
        return True
   
    def get_active_license_from_server(self,licenseFile):
        """
            parse the output from the license checker tool to get activated licenses from server
            output example :
                            License feature LICENSE_1: OK
                            License feature LICENSE_2 : OFF
             It looks for the line starts from 'License feature' and verify the status string after the colon(:)
        """
        if(licenseFile is not None):
            f = open(licenseFile, "r")
            for line in iter(f):
                line = line.strip()
                if line.startswith("License feature"):
                    if "OK" in line.split(":")[1]:
                        line = (line.split(":")[0]).split(" ")
                        self.activedLicense.append(line[2])
        else:
            raise ValueError("The given license file can not be found.") 

    def contain_sublist(self, list, sublist):
        """
        Check whether the list contains sublist
        """
        counter = 0
        for index in range(0,len(sublist)):
            if (str(sublist[index]) in list):
                counter +=1
        if (str(counter) != "0" and str(counter) == str(len(sublist))):
            return True
        return False

    def merge_lists(self, list1, list2):
        """
        Combine both lists into a new list
        """
        returnList = []
        for item in list1:
            returnList.append(item)
        for item in list2:
            returnList.append(item)
        return returnList