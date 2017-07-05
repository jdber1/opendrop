import sys
import os
import opendrop
import contact_angle

PENDANTDROP_REGION = os.path.join(os.path.dirname(os.path.realpath(__file__))+'/files', "pendantdrop_region.csv")
SESSILEDROP_REGION = os.path.join(os.path.dirname(os.path.realpath(__file__))+'/files', "sessiledrop_region.csv")
CONTACTAN_REGION = os.path.join(os.path.dirname(os.path.realpath(__file__))+'/files', "contactAn_region.csv")
CONTACTANNEEDLE_REGION = os.path.join(os.path.dirname(os.path.realpath(__file__))+'/files', "contactAnNeedle_region.csv")

def main():
    if sys.argv[1].startswith('--'):
        option = sys.argv[1][2:]
    # fetch sys.argv[1] but without the first two characters
    
    if cmp('pendantDrop',option):  #
        #print ('pendantDrop')
        opendrop.opendrop(1,PENDANTDROP_REGION)
    elif cmp('sessileDrop',option):  #
        #print ('sessileDrop')
        opendrop.opendrop(2,SESSILEDROP_REGION)
    elif cmp('contactAn',option):   #
        #print ('contactAn')
        contact_angle.contactAngle(1,CONTACTAN_REGION)
    elif cmp('contactAnNeedle',option):
        #print ('contactAnNeedle')
        contact_angle.contactAngle(2,CONTACTANNEEDLE_REGION)
    else:
        print ('wrong arguments for autotest')





if __name__ == '__main__':
    main()
