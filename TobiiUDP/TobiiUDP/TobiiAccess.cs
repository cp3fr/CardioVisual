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
    public class TobiiAccess
    {
        
        //initialize static variables
        private static Host _host;
        private static GazePointDataStream _gazePointDataStream;
        private static HeadPoseStream _headPoseStream;
        private static double _xPos;
        private static double _yPos;
        private static double _xAng;
        private static double _yAng;
        private static double _zAng;
        private static string _ipAddress;
        private static int _portAddress;
        private IPEndPoint _sending_end_point;
        private Socket _sending_socket;
        private static bool _filt;

        //startup procedure, initializing variables, connecting to eytracker, rosmaster, and advertising the publishing topic
        public void Startup()
        {
            //initialize variables
            _filt = false;
            _ipAddress = "127.0.0.1";
            _portAddress = 8808;
            _xPos = 0;
            _yPos = 0;
            _xAng = 0;
            _yAng = 0;
            _zAng = 0;

            //connect to eyetracker and ros
            InitUdp();
            ConnectEyetracker();
            OpenGazePointDataStream();
        }

        //sync method for accessing gaze point stream data and publishing the message
        public void GazeStreamMessagePublishing()
        {
            //This is the tobii gaze point data stream, which allows to access current gaze points and timestamps info
            //note that his stream function will not be left unless any key is pressed, therefore
            //use it as a wrapper function to perform ros communication and message publishing within it's ACTION field
            _gazePointDataStream.GazePoint((x, y, ts) =>
            {
                //update global variables using current values from local gaze stream
                UpdateGazePointGlobal(x, y);
                //if connected to ros and publisher, publish gaze point message and count
                //failed attempts to evaluate the connection status with ros
                SendMessage();
            });
        }

        //sync method for accessing gaze point stream data and publishing the message
        public void HeadStreamMessageUpdate()
        {
            //This is the tobii gaze point data stream, which allows to access current gaze points and timestamps info
            //note that his stream function will not be left unless any key is pressed, therefore
            //use it as a wrapper function to perform ros communication and message publishing within it's ACTION field
            _headPoseStream.HeadPose((ts, pos, rot) =>
            {
                //update global variables using current values from local gaze stream
                //note that for tobii headPose, rotation: x=pitch y=yaw z=roll
                //whereas for ros image coordinates are: x=to the right y=down
                //for now account for this by swapping x-y order to the Point message
                //also invert the axis direction
                UpdateHeadPoseGlobal(-rot.Y * 100000.0, rot.X * 100000.0, -rot.Z * 100000.0);
            });
        }

        //cleanup procedure, unadvertising the publisher, disconnecting from rosmaster, closing connection with eyetracker
        public void Cleanup()
        {
            DisconnectEyetracker();
        }

        //open udp port
        public void InitUdp()
        {
            //opening a udp socket
            _sending_socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram,
            ProtocolType.Udp);
            //setting the ip address
            IPAddress send_to_address = IPAddress.Parse(_ipAddress);
            //making an object for message sending
            _sending_end_point = new IPEndPoint(send_to_address, _portAddress);
            //return the object
        }

        //connect to eyetracker
        public void ConnectEyetracker()
        {
            _host = new Host();
        }

        //disconnect eyetracker
        public void DisconnectEyetracker()
        {
            _host.DisableConnection();
        }

        //open the gaze point data stream
        public void OpenGazePointDataStream()
        {
            //gaze position data stream
            //filtered data
            if (_filt)
            {
                //_gazePointDataStream = _host.Streams.CreateGazePointDataStream();
                _gazePointDataStream = _host.Streams.CreateGazePointDataStream(GazePointDataMode.LightlyFiltered);
            }
            //unfiltered data
            else
            {
                _gazePointDataStream = _host.Streams.CreateGazePointDataStream(GazePointDataMode.Unfiltered);
            }

            //head rotation data stream
            _headPoseStream = _host.Streams.CreateHeadPoseStream();
        }

        //method for updating global variables
        public void UpdateGazePointGlobal(double x, double y)
        {
            _xPos = x;
            _yPos = y;
        }

        //method for updating global variables
        public void UpdateHeadPoseGlobal(double x, double y, double z)
        {
            _xAng = x;
            _yAng = y;
            _zAng = z;
        }

        //sync method publishing a message
        public void SendMessage()
        {
            // this loads the string entered by the user into an array of bytes.

            string str = "p(" + _xPos.ToString("0.0000", System.Globalization.CultureInfo.InvariantCulture) + ", " 
                              + _yPos.ToString("0.0000", System.Globalization.CultureInfo.InvariantCulture) + ", " 
                              + _xAng.ToString("0.0000", System.Globalization.CultureInfo.InvariantCulture) + ", " 
                              + _yAng.ToString("0.0000", System.Globalization.CultureInfo.InvariantCulture) + ", " 
                              + _zAng.ToString("0.0000", System.Globalization.CultureInfo.InvariantCulture) + ")";
            byte[] send_buffer = Encoding.ASCII.GetBytes(str);
            //send the message
            try
            {
                Console.WriteLine(str);
                _sending_socket.SendTo(send_buffer, _sending_end_point);
            }
            catch (Exception send_exception)
            {
                Console.WriteLine(" Exception {0}", send_exception.Message);
            }
        }
    }
}

