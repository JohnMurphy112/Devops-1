import boto3
ec2 = boto3.resource('ec2')
inst_list =[]
for i in ec2.instances.all():
 inst_list.append(i)
 
while True:
 for it in range(len(inst_list)):
   
   try: 
      for tag in inst_list[it].tags:
        if tag['Key'] == 'Name':
         print(it,')',tag['Value'],inst_list[it].state)
   except:
       print(it,')','no name',inst_list[it].state) 
 choice = int(input('choose an instance to delete, type -1 to Exit '))
 if choice == -1:
  break
 
 inst_list[choice].terminate() 
 del inst_list[choice]
