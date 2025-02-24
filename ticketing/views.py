from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Ticket
from .serializers import TicketSerializer
from core.models import CustomUser


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.ROLE_CHOICES[4][0]:
            return Ticket.objects.all()
        return Ticket.objects.filter(customer=user)
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign_handler(self, request, pk=None):
        ticket = self.get_object()
        handler_id = request.data.get('handler_id')
        
        if not request.user.role == CustomUser.ROLE_CHOICES[4][0]:
            return Response(
                {"error": "Only supervisor members can assign handlers"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        ticket.handled_by_id = handler_id
        ticket.save()
        return Response(TicketSerializer(ticket).data)
    
    @action(detail=True, methods=['post'])
    def add_response(self, request, pk=None):
        ticket = self.get_object()
        response_text = request.data.get('response')
        
        if not (request.user.role == CustomUser.ROLE_CHOICES[4][0] or request.user == ticket.handled_by):
            return Response(
                {"error": "Only assigned handler or supervisor can add response"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        ticket.Response = response_text
        ticket.Response_Time = timezone.now()
        ticket.status = Ticket.TicketStatus.RESOLVED
        ticket.save()
        return Response(TicketSerializer(ticket).data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        
        if not (request.user.role == CustomUser.ROLE_CHOICES[4][0] or request.user == ticket.handled_by):
            return Response(
                {"error": "Only assigned handler or supervisor can change status"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if new_status not in dict(Ticket.TicketStatus.choices):
            return Response(
                {"error": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        ticket.status = new_status
        ticket.save()
        return Response(TicketSerializer(ticket).data)
    
    @action(detail=True, methods=['post'])
    def change_priority(self, request, pk=None):
        ticket = self.get_object()
        new_priority = request.data.get('priority')
        
        if not request.user.role == CustomUser.ROLE_CHOICES[4][0]:
            return Response(
                {"error": "Only supervisor members can change priority"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if new_priority not in dict(Ticket.TicketPriority.choices):
            return Response(
                {"error": "Invalid priority"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        ticket.priority = new_priority
        ticket.save()
        return Response(TicketSerializer(ticket).data)
