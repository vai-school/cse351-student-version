"""
Course: CSE 351, week 10
File: functions.py
Author: Lunden Vaile

Instructions:

Depth First Search
https://www.youtube.com/watch?v=9RHO6jU--GU

Breadth First Search
https://www.youtube.com/watch?v=86g8jAQug04


Requesting a family from the server:
family_id = 6128784944
data = get_data_from_server('{TOP_API_URL}/family/{family_id}')

Example JSON returned from the server
{
    'id': 6128784944, 
    'husband_id': 2367673859,        # use with the Person API
    'wife_id': 2373686152,           # use with the Person API
    'children': [2380738417, 2185423094, 2192483455]    # use with the Person API
}

Requesting an individual from the server:
person_id = 2373686152
data = get_data_from_server('{TOP_API_URL}/person/{person_id}')

Example JSON returned from the server
{
    'id': 2373686152, 
    'name': 'Stella', 
    'birth': '9-3-1846', 
    'parent_id': 5428641880,   # use with the Family API
    'family_id': 6128784944    # use with the Family API
}


--------------------------------------------------------------------------------------
You will lose 10% if you don't detail your part 1 and part 2 code below

Describe how to speed up part 1

Calling the server in its own set of threads. At the moment there is a slight bottleneck where each call takes about 0.25 seconds. while that wait happens no work is being done that.


Describe how to speed up part 2

Same wait and bottle neck happens on part 2 as well. Right now it waits for 1 gen at a time I would have it start another while the other one is finishing up.


Extra (Optional) 10% Bonus to speed up part 3

I think that the part 2 speedup would be a greater help here especially with no limit on the amount of threads. starting up other threads while the last of the previous are still joining

"""
from common import *
import threading

def dfs_worker(family_id, tree, tree_lock):
    child_threads = []
    found_people = []
    grandparent_threads = []

    response = get_data_from_server(f"{TOP_API_URL}/family/{family_id}")

    if response is not None:

        fam = Family(response)

        with tree_lock:
            tree.add_family(fam)

        member_ids = []
        member_ids.append(fam.get_husband())
        member_ids.append(fam.get_wife())
        member_ids.extend(fam.get_children())

        for pid in member_ids:
            t = threading.Thread(target=worker, args=(pid, found_people, threading.Semaphore()))
            t.start()
            child_threads.append(t)

        for t in child_threads:
            t.join()

        for person in found_people:
            mom_dad_id = person.get_parentid()

            if mom_dad_id is not None and not tree.does_family_exist(mom_dad_id):
                t = threading.Thread(target=dfs_worker, args=(mom_dad_id, tree, tree_lock))
                t.start()
                grandparent_threads.append(t)

        with tree_lock:
            for person in found_people:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)

    for t in grandparent_threads:
        t.join()

def worker(person_id, result_list, semaphore):
    endpoint = f"{TOP_API_URL}/person/{person_id}"

    with semaphore:
        response = get_data_from_server(endpoint)

    new_person = Person(response)

    result_list.append(new_person)

def depth_fs_pedigree(family_id, tree):
    shared_lock = threading.Lock()

    dfs_worker(family_id, tree, shared_lock)

def bfs_worker(family_id, pending_queue, tree, tree_lock, semaphore):
    with semaphore:
        response = get_data_from_server(f"{TOP_API_URL}/family/{family_id}")

    if response is not None:

        fam = Family(response)
        with tree_lock:
            tree.add_family(fam)

        member_ids = []
        member_ids.append(fam.get_husband())
        member_ids.append(fam.get_wife())
        member_ids.extend(fam.get_children())

        fetch_threads = []
        found_people = []
        for pid in member_ids:
            t = threading.Thread(target=worker, args=(pid, found_people, semaphore))
            t.start()
            fetch_threads.append(t)

        for t in fetch_threads:
            t.join()

        for person in found_people:
            mom_dad_id = person.get_parentid()

            if mom_dad_id is not None and not tree.does_family_exist(mom_dad_id):
                pending_queue.append(mom_dad_id)

        with tree_lock:
            for person in found_people:
                if not tree.does_person_exist(person.get_id()):
                    tree.add_person(person)

def breadth_fs_pedigree(family_id, tree):
    pending = [family_id]
    lock = threading.Lock()
    unlimited_semaphore = threading.Semaphore(2**31-1)

    while pending:
        threads = []
        for _ in range(len(pending)):
            fam_id = pending.pop(0)
            t = threading.Thread(target=bfs_worker, args=(fam_id, pending, tree, lock, unlimited_semaphore))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

def breadth_fs_pedigree_limit5(family_id, tree):
    pending = [family_id]
    lock = threading.Lock()
    conn_semaphore = threading.Semaphore(5)

    while pending:
        threads = []
        for _ in range(len(pending)):
            fam_id = pending.pop(0)
            t = threading.Thread(target=bfs_worker, args=(fam_id, pending, tree, lock, conn_semaphore))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()