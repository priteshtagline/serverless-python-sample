import json
import logging
import os

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

log = logging.getLogger()
log.setLevel(logging.DEBUG)


def get_paginated_list(sorted_result, url, start, limit):
    start = int(start)
    limit = int(limit)
    count = len(sorted_result)
    if count < start or limit < 0:
        return []

    obj = {}
    obj['start'] = start
    obj['limit'] = limit
    obj['count'] = count

    if start == 1:
        obj['previous'] = ''
    else:
        start_copy = max(1, start - limit)
        limit_copy = start - 1
        obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit_copy)

    if start + limit > count:
        obj['next'] = ''
    else:
        start_copy = start + limit
        obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)

    obj['story'] = sorted_result[(start - 1):(start - 1 + limit)]

    return obj


def list_stories(event, context):
    try:
        headers = {'x-hasura-admin-secret': os.environ["HASURA_ADMIN_SECRET"]}
        log.info(f"headers {headers}")
        transport = AIOHTTPTransport(
            url=os.environ["HASURA_GRAPHQL_API"], headers=headers)
        log.info(f"GraphQL API {os.environ['HASURA_GRAPHQL_API']}")

        client = Client(transport=transport, fetch_schema_from_transport=True)
        query_params = event["queryStringParameters"]
        login_user_id = query_params.get('user_id')

        if not login_user_id:
            log.info("user_id is missing in the query params")
            return {
                "statusCode": 400,
                "body": "user_id is missing in the query params"
            }

        query = gql(
            """
            query MyQuery {
                Stories {
                    User {
                        Followers_aggregate {
                            aggregate {
                            count
                            }
                        }
                        Followers {
                            follower_id
                        }
                        Following {
                            user_id
                        }
                        dob
                        first
                        gender
                        id
                        interestedin
                        last
                        lookingfor
                        mobile
                        photo
                        discreet_mode
                        Stories {
                            audio_url
                            created_at
                            duration
                            id
                            title
                            type
                            userid
                        }
                        age
                        agePref
                        genderPref
                        distancePref
                        lat
                        long
                        lastSeen
                    }
                    id
                    audio_url
                    created_at
                    duration
                    title
                    type
                    userid
                    Story_tags {
                        story_id
                        tag_id
                        Tag {
                            id
                            value
                        }
                    }
                    Replies_to_post_count: Comments_aggregate {
                        aggregate {
                            count
                        }
                    }
                    Voice_response_to_post_count: Comments_aggregate {
                        aggregate {
                            count(columns: audio_url)
                        }
                    }
                }
                favored_stories {
                        story_id
                    }
            }
            """
        )
        result = client.execute(query)

        for story in result["Stories"]:
            for following in story["User"]["Following"]:
                if login_user_id == following["user_id"]:
                    User_following_author = 10
                else:
                    User_following_author = 0

            for followers in story["User"]["Followers"]:
                if login_user_id == followers["follower_id"]:
                    User_followers_author = 10
                else:
                    User_followers_author = 0

            Favored_Stories_Count = 0
            for Favored_Stories in result["favored_stories"]:
                if Favored_Stories["story_id"] == story["id"]:
                    Favored_Stories_Count = Favored_Stories_Count + 1

            No_of_Story_Auth_Followers = story["User"]["Followers_aggregate"]["aggregate"]["count"]*40
            No_of_Favored_Stories = Favored_Stories_Count*30
            No_of_Comments = story["Replies_to_post_count"]["aggregate"]["count"]*30
            No_of_people_follow_author = story["User"]["Followers_aggregate"]["aggregate"]["count"]*10
            No_of_Voice_response = story["Voice_response_to_post_count"]["aggregate"]["count"]*10
            story_rank = (No_of_Story_Auth_Followers
                          + No_of_Favored_Stories
                          + No_of_Comments
                          + No_of_people_follow_author
                          + No_of_Voice_response
                          + User_following_author
                          + User_followers_author
                          )
            story["story_rank"] = story_rank

        sorted_result = sorted(
            result["Stories"], key=lambda d: d['story_rank'], reverse=True)
        log.info("Returning response")
        response = {
            "statusCode": 200,
            "body": json.dumps(get_paginated_list(sorted_result, '/story', start=query_params.get('start', 1), limit=query_params.get('limit', 5)))
        }
        return response
    except Exception as e:
        log.info(str(e))
        return {
            "statusCode": 500,
            "body": str(e)
        }

# print(list_stories({"user_id": "2c31448e-ac11-44a4-9170-88d864177bc9"}, "3"))
