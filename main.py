import lark_oapi as lark
import json
import pandas as pd
from os import environ
from datetime import datetime
from dotenv import load_dotenv
from lark_oapi.api.task.v2 import *
from lark_oapi.api.contact.v3 import *

load_dotenv()
user_Access_Token = environ.get("USER_ACCESS_TOKEN")
task_Guid = environ.get("TASK_GUID")

def process_task_data(task_data):
    """
    从任务数据中提取所需信息并转换格式
    """
    processed_data = {
        '任务项': task_data['summary'],
        '创建人': GetNameByUserID(task_data['creator']['id']),
        '任务创建时间': TimeChange(task_data['created_at'])
    }

    return processed_data

def main():
    listOfTasks_response = GetListOfTasksRequest()

    # 处理业务结果
    #lark.logger.info(lark.JSON.marshal(response.data, indent=4))

    json_str = lark.JSON.marshal(listOfTasks_response.data, indent=4)
    data = json.loads(json_str)

    processed_data = process_task_data(data['task'])
    df = pd.DataFrame([processed_data])

    writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)

    workbook = writer.book
    worksheet = writer.sheets['Sheet1']

    for i, col in enumerate(df.columns):
        column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.set_column(i, i, column_len)

    # 保存Excel文件
    writer.close()

    print("ok")

def init():
    client = lark.Client.builder() \
        .enable_set_token(True) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()
    return client

def GetListOfTasksRequest():
    client  = init()
    request: GetTaskRequest = GetTaskRequest.builder() \
        .task_guid(task_Guid) \
        .user_id_type("open_id") \
        .build()

    option = lark.RequestOption.builder().user_access_token(user_Access_Token).build()
    response: GetTaskResponse = client.task.v2.task.get(request, option)
    if not response.success():
            lark.logger.error(
                f"client.task.v2.task.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
            return

    return response

def GetUserNameRequest(userID):
    client  = init()
    request: GetUserRequest = GetUserRequest.builder() \
        .user_id(userID) \
        .user_id_type("open_id") \
        .department_id_type("open_department_id") \
        .build()
    
    option = lark.RequestOption.builder().user_access_token(user_Access_Token).build()
    response: GetUserResponse = client.contact.v3.user.get(request, option)
    if not response.success():
        lark.logger.error(
            f"client.contact.v3.user.get failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return
    
    return response

def GetNameByUserID(userID):
    response_data = json.loads(lark.JSON.marshal(GetUserNameRequest(userID).data, indent=4))
    try:
        name = response_data['user']['name']
        return name
    except KeyError as e:
        print(f"KeyError: {e}")
        return None

def TimeChange(unixTime):
    timestamp = int(unixTime) / 1000
    return datetime.fromtimestamp(timestamp)

if __name__ == "__main__":
    main()