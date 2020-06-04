from flask import abort, jsonify, Response, status
from flask.views import MethodView
from app.models import AuthSMS
class APIView(MethodView):
    """ Generic API, all the API views will inherit for this base class
        every dispatch method will return an invalid request message, every
        child class must implements this methods properly
        More info about flask class based views here
        http://flask.pocoo.org/docs/views/#method-based-dispatching.
    """

    ENDPOINT = '/api/v0.3'

    def get(self):
        abort(400)

    def post(self):
        abort(400)

    def put(self):
        abort(400)

    def delete(self):
        abort(400)

    def json_response(self, data={}):
        return jsonify(data)

class AuthSMS(APIView):
    def post(self, request):
        try:
            p_num = request.data['phone_number']
        except KeyError:
            return Response({'message' : 'Bad Request'},
            status=status.HTTP_400_BAD_REQUEST)
        else:
            AuthSMS.objects.update_or_create(phone_number=p_num)
            return Response({'message': 'OK'})

    def get(self, request):
        try:
            p_num = request.query_params['phone_number']
            a_num = request.query_params['auth_number']
        except KeyError:
            return Response({'message' : 'Bad Request'},
            status=status.HTTP_400_BAD_REQUEST)
        else:
            result = AuthSMS.check_auth_number(p_num, a_num)
            return Response({'message' : 'OK', 'result' : result})
