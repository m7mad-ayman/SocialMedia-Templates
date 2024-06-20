from django.db.models import QuerySet
from django.db.models.sql.query import Query
from django.shortcuts import render,redirect
from django.http import response
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .models import *
import random
# Create your views here.
@login_required(login_url='signin')
def index(request):
    posts = Post.objects.none()
    exceptions = []
    relation =Follow.objects.filter(follower=request.user)
    for follow in relation:
        if follow.value == "Following":
            user= get_user_model()
            user=user.objects.get(username=follow.followed)
            profile = Profile.objects.get(user=user)
            exceptions.append(profile)
            post_user=Post.objects.filter(profile=profile)
            posts=posts | post_user
        else:
            continue
    profile= Profile.objects.get(user=request.user)
    exceptions.append(profile)
    allp = set(Profile.objects.all())
    allp = allp-set(exceptions)
    if len(allp)>=4:
       suggested = random.sample(list(allp),4)
    else:
        suggested = random.sample(list(allp),len(allp))
    if not posts:
        return render(request,"index.html",{"myprofile":profile,"message":"You don't follow any one","suggested":suggested})
    else:
        posts=posts.order_by("-created_at")
        
    
        
        """
        specify comments[important]
    
        for i in posts:
            for n in i.postr.all():
                print(n.comment.comment)
                """
        return render(request,"index.html",{"myprofile":profile,"posts":posts,"suggested":suggested})
   
def signin(request):
    if request.method =="POST":
        try:
           if "@" in request.POST['username']:
               username = request.POST["username"]
               password = request.POST["password"]
               user=auth.authenticate(email = request.POST['username'],password=request.POST['password'])
           else:
               username = request.POST["username"]
               password = request.POST["password"] 
               user=auth.authenticate(username = username,password=password)
           if user != None:
               auth.login(request,user)
               
               print('authenticated')
               return redirect("/")
           else:
               return render(request,"signin.html",{"message":"username or password isn't correct"})
        except Exception as ex:
           return render(request,"signin.html",{"message":"username or password isn't correct"})
    
        
    return render(request,"signin.html")


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect("/signin/")

def signup(request):
   if request.method=="POST":
      if request.POST.get('agree') == "on":
         User = get_user_model()
         if not User.objects.filter(username = request.POST.get('username')).exists(): 
            if "@" in str(request.POST.get('email')): 
                
                if request.POST.get('password') == request.POST.get('confirm'):
                    
                    user=User.objects.create_user(username =request.POST['username'],email=request.POST['email'],password=request.POST['password'])
                    user.save()
                    profile=Profile(user=user)
                    profile.save()
                    user=auth.authenticate(username = request.POST.get('username'),password=request.POST.get('password'))
                    if user != None:
                        
                        auth.login(request,user)
                        return redirect("/settings/")
                else:
                    return render(request,"signup.html",{"message":"passwords don't match"})
            else:
                return render(request,"signup.html",{"message":"email isn't valid"})
            
            
         else:
            return render(request,"signup.html",{"message":"username is already taken"})
      else: 
          return render(request,"signup.html",{"message":"You must agree the terms"}) 
      return redirect('/signin/')
   return render(request,"signup.html")
   
@login_required(login_url='signin')
def settings(request):
    return render(request,"settings.html")

@login_required(login_url='signin')
def myprofile(request):
    User = get_user_model()
    user=User.objects.get(username=request.user.username)
    profile = Profile.objects.get(user=user)
    posts = Post.objects.filter(profile=profile)
    
    return render(request,"myprofile.html",{"myprofile":profile,"username":request.user.username,"posts":posts})

@login_required(login_url='signin')
def like(request,id):
    username = request.user.username
    post_id = id
    if not Like.objects.filter(postid=id,username=username).exists():
        post = Post.objects.get(id=post_id)
        like = Like()
        like.postid = id
        like.username = username
        if like != None:
            like.save()
            post.likes +=1
            post.save()
    else:
        like = Like.objects.get(postid=id,username=username)
        post = Post.objects.get(id=post_id)
        like.delete()
        post.likes -=1
        post.save()
    return redirect("/")
        
@login_required(login_url='signin')
def comment(request,id):
    if request.method == "POST":
       if not request.POST["comment"] == None:
          user = request.user
          relatedpost=Post.objects.get(id=id)
          profile=Profile.objects.get(user=user)
          comment = Comment(postid=id,profile=profile,comment=request.POST['comment'])
          comment.save()
          relatedpost.no_comments+=1
          relatedpost.save()
          related = Relation(relatedpost=relatedpost,relatedcom=comment)
          related.save()
          return redirect("/")
       else:
          return redirect("/")
    else:
        return redirect('/') 
      
      
@login_required(login_url='signin')
def create_post(request):

    if request.method == "POST":
        if not request.FILES.get('picture') == None:
            profile=Profile.objects.get(user=request.user)
            image =request.FILES.get('picture')
            newpost = Post(profile=profile,image=image,caption=request.POST["caption"])
            newpost.save()
            profile.posts+=1
            profile.save()
            return redirect("/")
        else:
            return redirect("/")
    else:
        return redirect('/')
        

@login_required(login_url='signin')            
def profile(request,username):
    if username == request.user.username:
        return redirect("/myprofile")
    else:
        logedin = request.user
        User = get_user_model()
        user = User.objects.get(username=username)
        profile = Profile.objects.get(user=user)
        posts = Post.objects.filter(profile=profile)
        try:
            follow= Follow.objects.get(follower=logedin,followed=user)
            statue=follow.value
            return render(request,"profile.html",{"profile":profile,"statue":statue,"posts":posts})
        except:
            statue="Follow"
            return render(request,"profile.html",{"profile":profile,"statue":statue,"posts":posts})
    
    
    
    
@login_required(login_url='signin')            
def follow(request,username):
    if request.method=="POST":
        User=get_user_model()
        follower = request.user 
        followed = User.objects.get(username=username)
        if not Follow.objects.filter(follower=follower,followed=followed).exists():
            follower_profile = Profile.objects.get(user=follower)
            follower_profile.following +=1
            follower_profile.save()
            followed_profile =Profile.objects.get(user=followed)
            followed_profile.followers +=1
            followed_profile.save()
            follow = Follow(follower = follower,followed=followed,value="Following")
            if follow != None:
                follow.save()
                return redirect("/profile/{}".format(username))
            else:
                return redirect("/profile/{}".format(username))
        elif Follow.objects.get(follower=follower,followed=followed).value=="Follow":
            follower_profile = Profile.objects.get(user=follower)
            follower_profile.following +=1
            follower_profile.save()
            followed_profile =Profile.objects.get(user=followed)
            followed_profile.followers +=1
            followed_profile.save()
            follow = Follow.objects.get(follower=follower,followed=followed)
            follow.value = "Following"
            if follow != None:
                follow.save()
                return redirect("/profile/{}".format(username))
            else:
                return redirect("/profile/{}".format(username))
        else:
            follower_profile = Profile.objects.get(user=follower)
            follower_profile.following -=1
            follower_profile.save()
            followed_profile =Profile.objects.get(user=followed)
            followed_profile.followers -=1
            followed_profile.save()
            follow = Follow.objects.get(follower = follower,followed=followed)
            follow.value="Follow"
            
            if follow != None:
                follow.save()
                return redirect("/profile/{}".format(username))
            else:
                return redirect("/profile/{}".format(username))
    else:
        User=get_user_model()
        follower = request.user 
        followed = User.objects.get(username=username)
        follower_profile = Profile.objects.get(user=follower)
        follower_profile.following +=1
        follower_profile.save()
        followed_profile =Profile.objects.get(user=followed)
        followed_profile.followers +=1
        followed_profile.save()
        follow = Follow(follower=follower,followed=followed)
        follow.value = "Following"
        if follow != None:
           follow.save()
           return redirect("/")
        else:
            return redirect("/")
@login_required(login_url='signin')  
def delete_post(request,id):
    post = Post.objects.get(id=id)
    post.delete()
    return redirect('/myprofile/')

@login_required(login_url='signin')  
def search(request):
    if request.method=="POST":
        profiles=Profile.objects.none()
        username =str(request.POST["searchvalue"])
        User=get_user_model()
        users=User.objects.filter(username__contains=username)
        for user in users:
            profile = Profile.objects.filter(user=user)
            profiles=profiles|profile
        profile = Profile.objects.get(user=request.user)
        return render(request,"search.html",{"myprofile":profile,"username":username,"profiles":profiles})
    else:
        return redirect('/')
    
@login_required(login_url='signin')
def profilesettings(request):
    if request.method=="POST":
        profile = Profile.objects.get(user=request.user)
        if not request.FILES.get('picture') == None:
            image =request.FILES.get('picture')
            profile.img = image
        else:
            pass
        if request.POST["bio"]:
            profile.bio = request.POST["bio"]
        else:
            pass
        if profile != None:
            profile.save()
            return redirect('/myprofile')
        else:
            return redirect('/myprofile')
    else : 
        return redirect('/')
            
            