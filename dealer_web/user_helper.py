from api_helper import resp_to_lst, lst_to_tbl


def order_place_by_user(obj_client, kwargs):
    th, td, mh, md = [], [], [], []
    resp = obj_client.order_place(**kwargs)
    if resp:
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, client_name=obj_client.client_name)
        if 'message' in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def order_modify_by_user(obj_client, kwargs):
    th, td, mh, md = [], [], [], []
    resp = obj_client.order_modify(kwargs)
    print(kwargs)
    print(resp)
    lst = resp_to_lst(resp)
    th1, td1 = lst_to_tbl(lst, client_name=obj_client.client_name)
    if 'message' in th1:
        mh = th1
        md += td1
    else:
        th = th1
        td += td1
    return mh, md, th, td


def order_cancel_by_user(obj_client, order_id, variety):
    th, td, mh, md = [], [], [], []
    resp = obj_client.order_cancel(order_id, variety)
    lst = resp_to_lst(resp)
    th1, td1 = lst_to_tbl(lst, client_name=obj_client.client_name)
    if 'message' in th1:
        mh = th1
        md += td1
    else:
        th = th1
        td += td1
    return mh, md, th, td
