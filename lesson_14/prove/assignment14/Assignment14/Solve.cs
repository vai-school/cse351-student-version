using System.Collections.Concurrent;
using Newtonsoft.Json.Linq;

namespace Assignment14;

public static class Solve
{
    private static readonly HttpClient HttpClient = new()
    {
        Timeout = TimeSpan.FromSeconds(180)
    };
    public const string TopApiUrl = "http://127.0.0.1:8123";

    // This function retrieves JSON from the server
    public static async Task<JObject?> GetDataFromServerAsync(string url)
    {
        try
        {
            var jsonString = await HttpClient.GetStringAsync(url);
            return JObject.Parse(jsonString);
        }
        catch (HttpRequestException e)
        {
            Console.WriteLine($"Error fetching data from {url}: {e.Message}");
            return null;
        }
    }

    // This function takes in a person ID and retrieves a Person object
    // Hint: It can be used in a "new List<Task<Person?>>()" list
    private static async Task<Person?> FetchPersonAsync(long personId)
    {
        var personJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/person/{personId}");
        return personJson != null ? Person.FromJson(personJson.ToString()) : null;
    }

    // This function takes in a family ID and retrieves a Family object
    // Hint: It can be used in a "new List<Task<Family?>>()" list
    private static async Task<Family?> FetchFamilyAsync(long familyId)
    {
        var familyJson = await Solve.GetDataFromServerAsync($"{Solve.TopApiUrl}/family/{familyId}");
        return familyJson != null ? Family.FromJson(familyJson.ToString()) : null;
    }
    
    // =======================================================================================================
    public static async Task<bool> DepthFS(long familyId, Tree tree)
    {
        object treeLock = new object();
        await DepthWorker(familyId, tree, treeLock);
        return true;
    }

    private static async Task<bool> DepthWorker(long familyId, Tree tree, object treeLock)
    {
        List<Task<bool>> tasks = [];
        List<Person?> people = [];
        List<Task<Person?>> workers = [];

        Family? fam = await FetchFamilyAsync(familyId);

        if (fam is not null){

            lock (treeLock)
                tree.AddFamily(fam);

            List<long> member_ids = [];
            member_ids.Add(fam.HusbandId);
            member_ids.Add(fam.WifeId);
            member_ids.AddRange(fam.Children);

            foreach (long pid in member_ids){
                Task<Person?> worker = FetchPersonAsync(pid);
                workers.Add(worker);
            }

            await Task.WhenAll(workers); 

            foreach (var task in workers)
            {
                people.Add(task.Result);
            }

            foreach (Person? person in people)
            {
                if (person is not null)
                {
                   long momDadId = person.ParentId;

                   lock (treeLock)
                    {
                        if (!tree.DoesFamilyExist(momDadId)&& momDadId != 0)
                        {
                            Task<bool> task = DepthWorker(momDadId, tree, treeLock);
                            tasks.Add(task);
                        }
                    } 
                }
            }


            lock(treeLock){
                foreach (Person? person in people){
                    if (person is not null) 
                        if (!tree.DoesPersonExist(person.Id))
                            tree.AddPerson(person);
                }
            }
        }

        await Task.WhenAll(tasks);

        return true;

    }

    // =======================================================================================================
    public static async Task<bool> BreadthFS(long famid, Tree tree)
    {
        object treeLock = new object();
        ConcurrentQueue<long> familyIds = new ConcurrentQueue<long>();

        familyIds.Enqueue(famid);

        while(!familyIds.IsEmpty){
            List<Task<bool>> tasks = [];
            while (!familyIds.IsEmpty)
            {
                if (familyIds.TryDequeue(out long famId))
                {
                    Task<bool> task = BreadthWorker(famId, tree, treeLock, familyIds);
                    tasks.Add(task);
                }
            }
            await Task.WhenAll(tasks);
        }
        return true;
    }
    private static async Task<bool> BreadthWorker(long familyId, Tree tree, object treeLock, ConcurrentQueue<long> familyIds)
    {
        List<Person?> people = [];
        List<Task<Person?>> workers = [];

        Family? fam = await FetchFamilyAsync(familyId);

        if (fam is not null){

            lock (treeLock)
                tree.AddFamily(fam);

            List<long> member_ids = [];
            member_ids.Add(fam.HusbandId);
            member_ids.Add(fam.WifeId);
            member_ids.AddRange(fam.Children);

            foreach (long pid in member_ids){
                Task<Person?> worker = FetchPersonAsync(pid);
                workers.Add(worker);
            }

            await Task.WhenAll(workers); 

            foreach (var task in workers)
            {
                people.Add(task.Result);
            }

            foreach (Person? person in people)
            {
                if (person is not null)
                {
                   long momDadId = person.ParentId;

                   lock (treeLock)
                    {
                        if (!tree.DoesFamilyExist(momDadId)&& momDadId != 0)
                            familyIds.Enqueue(momDadId);
                           
                    } 
                }
            }


            lock(treeLock){
                foreach (Person? person in people){
                    if (person is not null) 
                        if (!tree.DoesPersonExist(person.Id))
                            tree.AddPerson(person);
                }
            }
        }

        return true;

    }


}
