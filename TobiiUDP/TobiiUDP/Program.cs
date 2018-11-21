using System;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;
using Tobii.Interaction;
using Tobii.Interaction.Framework;

namespace TobiiUDP
{
    public class Program
    {
        public static void Main(string[] args)
        {
            //initialized local variable storing the pushed keys
            ConsoleKeyInfo userResponse;
            //initialize obj to handle the various program functions
            TobiiAccess obj = new TobiiAccess();
            //startup procedure: initialize variables, connect to eyetracker, 
            //rosmaster, and advertise topic to be published
            obj.Startup();
            //repeat the following tasks until escape key is pressed
            do
            {
                //method giving access to tobii gaze point data stream,
                //regularly checking for connection with rosmaster and publisher
                //saving updating global gaze point variables with current local values
                //and sending gaze point messages to rosmaster
                obj.HeadStreamMessageUpdate();
                obj.GazeStreamMessagePublishing();
                //listen to keypress 
                userResponse = Console.ReadKey(true);
                //..exit the loop when escape key was pressed
            } while (userResponse.Key != ConsoleKey.Escape);
            //cleanup: unadvertise publisher, disconnect from rosmaster, disconnect
            //from eyetracker
            obj.Cleanup();
        }
    }
}

