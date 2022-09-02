import os
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_paginate import Pagination, get_page_args

load_dotenv()

headers = {'x-hasura-admin-secret': os.environ["HASURA_ADMIN_SECRET"] }
transport = AIOHTTPTransport(url=os.environ["HASURA_GRAPHQL_API"], headers=headers)
client = Client(transport=transport, fetch_schema_from_transport=True)

app = Flask(__name__)

def get_stories(stories,offset=0, per_page=10):
    return stories[offset: offset + per_page]

@app.route("/")
def index():
    return "Kite App Backend"


@app.route("/story/")
def story():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    query = gql(
        """
        query MyQuery {
            Stories {
                audio_url
                created_at
                duration
                id
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
                User {
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
                    discreet_mode
                }
            }
        }
        """
    )
    result = client.execute(query)

    pagination_stories = get_stories(result["Stories"],offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=len(result["Stories"]),css_framework='bootstrap4')

    return jsonify({"story":pagination_stories,"pagination":pagination.links})

if __name__ == "__main__":
    app.run(debug=True)