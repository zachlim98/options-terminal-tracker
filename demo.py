import easygui

msg = "Enter your personal information"
title = "Credit Card Application"
fieldNames = ["Name", "Street Address", "City", "State", "ZipCode"]
fieldValues = easygui.multenterbox(msg, title, fieldNames)

print(f"Your name is {fieldValues[0]} and you live in {fieldValues[2]}")